from typing import Any, Iterator, Protocol
import json
import threading
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

import requests

from vereda_ai.core.config import settings
from vereda_ai.core.logging import get_logger
from vereda_ai.syntexa_core.runtime_model import runtime_ready_for_active_model


ProviderName = str

logger = get_logger(__name__)
_LLM_SEMAPHORE = threading.BoundedSemaphore(
    max(1, int(getattr(settings, "llm_max_concurrency", 4)))
)
_SOFT_FALLBACK_TEXT = "Resposta gerada pelo motor local da Syntexa."  # usado apenas pelo DummyLLMProvider


class LLMProvider(Protocol):
    name: ProviderName

    def chat(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        ...

    def embed(self, texts: list[str], **kwargs: Any) -> list[list[float]]:
        ...


class DummyLLMProvider:
    """
    REMOVIDO DO PIPELINE (V38).
    Não pode existir fallback fake. Levanta RuntimeError para forçar fail fast.
    """
    name: ProviderName = "dummy"

    def chat(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        raise RuntimeError(
            "[Syntexa V38] Nenhum provedor LLM real disponível. "
            "Configure OLLAMA_ENDPOINT, LOCAL_LLM_ENDPOINT, VLLM_ENDPOINT, "
            "ou garanta que o motor neural local Syntexa esteja ativo."
        )

    def chat_stream(self, messages: list[dict[str, Any]], **kwargs: Any) -> Iterator[str]:
        raise RuntimeError(
            "[Syntexa V38] Nenhum provedor LLM real disponível. "
            "Configure OLLAMA_ENDPOINT, LOCAL_LLM_ENDPOINT, VLLM_ENDPOINT, "
            "ou garanta que o motor neural local Syntexa esteja ativo."
        )

    def embed(self, texts: list[str], **kwargs: Any) -> list[list[float]]:
        return [[float(len(t))] for t in texts]


class SyntexaNativeLLMProvider:
    """
    Núcleo proprietário (Fase 1): NLP híbrido interno — sem APIs de modelos de terceiros.
    Substituição gradual: checkpoints em `training/` + registry em `config/syntexa_model_registry.json`.
    """

    name: ProviderName = "syntexa_native"

    def chat(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        # Chama a instância AWS com o modelo Syntexa próprio (34M params)
        url = "http://54.210.101.255:8000/generate"
        payload = {
            "messages": messages,
            "max_new_tokens": kwargs.get("max_tokens", 80),
            "temperature": kwargs.get("temperature", 0.7),
        }
        try:
            resp = requests.post(url, json=payload, timeout=(5, 60))
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "")
        except Exception as exc:
            logger.warning("AWS LLM falhou: %s", exc)
            return f"[Erro: modelo não respondeu — {exc}]"

    def chat_stream(self, messages: list[dict[str, Any]], **kwargs: Any) -> Iterator[str]:
        # Por enquanto entrega tudo de uma vez (servidor AWS não suporta stream ainda)
        yield self.chat(messages, **kwargs)

    def embed(self, texts: list[str], **kwargs: Any) -> list[list[float]]:
        from vereda_ai.syntexa_core.hybrid_engine import native_embed

        return native_embed(texts)


class HTTPJSONLLMProvider:
    """
    Provedor genérico para servidores de LLM compatíveis com API estilo OpenAI
    (inclui gateways com vLLM, servidores próprios, Cloudflare Workers, etc.).
    """

    def __init__(self, name: ProviderName, base_url: str, api_key: str | None = None):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _post_with_retry(
        self,
        path: str,
        *,
        payload: dict[str, Any],
        timeout: float | tuple[float, float] | None = None,
    ) -> requests.Response:
        attempts = max(1, int(getattr(settings, "llm_retry_count", 3)))
        backoff_ms = max(0, int(getattr(settings, "llm_retry_backoff_ms", 150)))
        connect_timeout = float(getattr(settings, "llm_connect_timeout", 3.0))
        read_timeout = float(getattr(settings, "llm_read_timeout", 120.0))
        req_timeout = timeout if timeout is not None else (connect_timeout, read_timeout)
        url = f"{self.base_url}{path}"
        last_exc: Exception | None = None
        for i in range(attempts):
            try:
                with _LLM_SEMAPHORE:
                    resp = requests.post(
                        url,
                        json=payload,
                        headers=self._headers(),
                        timeout=req_timeout,
                    )
                resp.raise_for_status()
                return resp
            except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as exc:
                last_exc = exc
                logger.warning(
                    "Falha ao chamar HTTP LLM (tentativa %s/%s): %s",
                    i + 1,
                    attempts,
                    exc,
                )
                if i >= attempts - 1:
                    raise
                time.sleep((backoff_ms * (2**i)) / 1000.0)
        if last_exc:
            raise last_exc
        raise RuntimeError("Falha inesperada em _post_with_retry")

    def chat(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        payload: dict[str, Any] = {
            "model": kwargs.get("model", "syntexa-large"),
            "messages": messages,
        }
        if "temperature" in kwargs:
            payload["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            payload["max_tokens"] = kwargs["max_tokens"]

        _to = kwargs.get("timeout")
        if _to is None:
            _to = (
                float(getattr(settings, "llm_connect_timeout", 3.0)),
                float(getattr(settings, "llm_read_timeout", 120.0)),
            )
        resp = self._post_with_retry(
            "/v1/chat/completions",
            payload=payload,
            timeout=_to,
        )
        data = resp.json()
        choices = data.get("choices") or []
        if not choices:
            return "[HTTP LLM] Nenhuma escolha retornada."
        message = choices[0].get("message") or {}
        return str(message.get("content", ""))

    def embed(self, texts: list[str], **kwargs: Any) -> list[list[float]]:
        payload: dict[str, Any] = {
            "model": kwargs.get("model", "syntexa-embed"),
            "input": texts,
        }
        resp = self._post_with_retry(
            "/v1/embeddings",
            payload=payload,
            timeout=kwargs.get("timeout", 60),
        )
        data = resp.json()
        embeddings = data.get("data") or []
        return [e.get("embedding", []) for e in embeddings]

    def _stream_openai_sse(self, path: str, payload: dict[str, Any]) -> Iterator[str]:
        """
        POST com stream=True e leitura incremental (não bufferiza a resposta inteira).
        """
        connect_timeout = float(getattr(settings, "llm_connect_timeout", 3.0))
        read_timeout = float(getattr(settings, "llm_stream_read_timeout", 900.0))
        url = f"{self.base_url}{path}"
        attempts = max(1, int(getattr(settings, "llm_retry_count", 3)))
        backoff_ms = max(0, int(getattr(settings, "llm_retry_backoff_ms", 150)))
        last_exc: Exception | None = None
        for i in range(attempts):
            resp: requests.Response | None = None
            try:
                with _LLM_SEMAPHORE:
                    resp = requests.post(
                        url,
                        json=payload,
                        headers=self._headers(),
                        stream=True,
                        timeout=(connect_timeout, read_timeout),
                    )
                resp.raise_for_status()
                try:
                    for line in resp.iter_lines(decode_unicode=True):
                        if not line:
                            continue
                        text = line.strip()
                        raw: str | None = None
                        if text.startswith("data:"):
                            raw = text[5:].strip()
                            if raw == "[DONE]":
                                break
                        elif text.startswith("{"):
                            raw = text
                        else:
                            continue
                        if not raw:
                            continue
                        try:
                            item = json.loads(raw)
                        except json.JSONDecodeError:
                            continue
                        choices = item.get("choices") or []
                        if not choices:
                            continue
                        ch0 = choices[0]
                        delta = ch0.get("delta") or {}
                        content = str(delta.get("content") or "")
                        if not content:
                            msg = ch0.get("message") or {}
                            content = str(msg.get("content") or "")
                        if not content:
                            content = str(ch0.get("text") or "")
                        if content:
                            yield content
                finally:
                    if resp is not None:
                        resp.close()
                return
            except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as exc:
                last_exc = exc
                if resp is not None:
                    try:
                        resp.close()
                    except Exception:
                        pass
                logger.warning(
                    "Falha stream HTTP LLM (tentativa %s/%s): %s",
                    i + 1,
                    attempts,
                    exc,
                )
                if i >= attempts - 1:
                    raise
                time.sleep((backoff_ms * (2**i)) / 1000.0)
        if last_exc:
            raise last_exc
        raise RuntimeError("Falha inesperada em _stream_openai_sse")

    def chat_stream(self, messages: list[dict[str, str]], **kwargs: Any) -> Iterator[str]:
        payload: dict[str, Any] = {
            "model": kwargs.get("model", "syntexa-large"),
            "messages": messages,
            "stream": True,
        }
        if "temperature" in kwargs:
            payload["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            payload["max_tokens"] = kwargs["max_tokens"]

        yield from self._stream_openai_sse("/v1/chat/completions", payload)


class OllamaLLMProvider(HTTPJSONLLMProvider):
    """
    Geração de texto via Ollama (API compatível OpenAI: `/v1/chat/completions`).
    Embeddings ficam no núcleo Syntexa Native (RAG, memória, treino) — o modelo Ollama só gera texto.
    """

    def __init__(self, base_url: str, model: str, api_key: str | None = None):
        super().__init__(name="ollama", base_url=base_url, api_key=api_key)
        self._ollama_model = (model or "llama3.2").strip()
        self._native_for_embed = SyntexaNativeLLMProvider()

    def chat(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        kwargs.setdefault("model", self._ollama_model)
        return super().chat(messages, **kwargs)

    def chat_stream(self, messages: list[dict[str, Any]], **kwargs: Any) -> Iterator[str]:
        kwargs.setdefault("model", self._ollama_model)
        yield from super().chat_stream(messages, **kwargs)

    def embed(self, texts: list[str], **kwargs: Any) -> list[list[float]]:
        from vereda_ai.knowledge.open_embedding_backend import embed_ollama, hash_embed_texts

        mod = (
            kwargs.get("model")
            or getattr(settings, "ollama_embed_model", None)
            or "nomic-embed-text"
        )
        try:
            v = embed_ollama(self.base_url, str(mod).strip(), texts)
            if v and len(v) == len(texts):
                return v
        except Exception as exc:
            logger.warning("Ollama /api/embed falhou; fallback hash: %s", exc)
        return hash_embed_texts(texts)


class OpenAIProvider(HTTPJSONLLMProvider):
    name: ProviderName = "openai"

    def __init__(self, base_url: str, api_key: str, model: str):
        super().__init__(name="openai", base_url=base_url, api_key=api_key)
        self._model = (model or "gpt-4o-mini").strip()

    def chat(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        kwargs.setdefault("model", self._model)
        return super().chat(messages, **kwargs)

    def chat_stream(self, messages: list[dict[str, Any]], **kwargs: Any) -> Iterator[str]:
        kwargs.setdefault("model", self._model)
        yield from super().chat_stream(messages, **kwargs)


class DeepSeekProvider(HTTPJSONLLMProvider):
    """DeepSeek API — compatível OpenAI (/v1/chat/completions)."""
    name: ProviderName = "deepseek"

    def __init__(self, base_url: str, api_key: str, model: str):
        super().__init__(name="deepseek", base_url=base_url, api_key=api_key)
        self._model = (model or "deepseek-chat").strip()

    def chat(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        kwargs.setdefault("model", self._model)
        return super().chat(messages, **kwargs)

    def chat_stream(self, messages: list[dict[str, Any]], **kwargs: Any) -> Iterator[str]:
        kwargs.setdefault("model", self._model)
        yield from super().chat_stream(messages, **kwargs)


class GeminiProvider(HTTPJSONLLMProvider):
    """Google Gemini via endpoint OpenAI-compatible (/v1beta/openai/chat/completions)."""
    name: ProviderName = "gemini"

    def __init__(self, base_url: str, api_key: str, model: str):
        super().__init__(name="gemini", base_url=base_url, api_key=api_key)
        self._model = (model or "gemini-1.5-flash").strip()

    def chat(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        kwargs.setdefault("model", self._model)
        return super().chat(messages, **kwargs)

    def chat_stream(self, messages: list[dict[str, Any]], **kwargs: Any) -> Iterator[str]:
        kwargs.setdefault("model", self._model)
        yield from super().chat_stream(messages, **kwargs)


class AnthropicProvider(HTTPJSONLLMProvider):
    """
    Anthropic Claude via Messages API.
    Converte mensagens OpenAI-style para formato Anthropic e converte a resposta de volta.
    Streaming via SSE compatível (eventos de texto progressivo).
    """
    name: ProviderName = "anthropic"

    def __init__(self, base_url: str, api_key: str, model: str):
        # Anthropic base padrão: https://api.anthropic.com
        super().__init__(name="anthropic", base_url=base_url, api_key=api_key)
        self._model = (model or "claude-3-5-sonnet-20241022").strip()

    def _to_anthropic_messages(self, messages: list[dict[str, Any]]) -> tuple[str | None, list[dict[str, Any]]]:
        """Extrai system prompt e converte restante para formato Anthropic."""
        system_text: str | None = None
        anthropic_msgs: list[dict[str, Any]] = []
        for m in messages:
            role = (m.get("role") or "").lower()
            content = str(m.get("content") or "")
            if role == "system":
                system_text = content
                continue
            if role in ("user", "assistant"):
                anthropic_msgs.append({"role": role, "content": content})
        return system_text, anthropic_msgs

    def chat(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        system_text, anthropic_msgs = self._to_anthropic_messages(messages)
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": anthropic_msgs,
            "max_tokens": kwargs.get("max_tokens", 4096),
        }
        if system_text:
            payload["system"] = system_text
        if "temperature" in kwargs:
            payload["temperature"] = kwargs["temperature"]
        _to = kwargs.get("timeout")
        if _to is None:
            _to = (
                float(getattr(settings, "llm_connect_timeout", 3.0)),
                float(getattr(settings, "llm_read_timeout", 120.0)),
            )
        resp = self._post_with_retry("/v1/messages", payload=payload, timeout=_to)
        data = resp.json()
        content_blocks = data.get("content") or []
        out_parts: list[str] = []
        for block in content_blocks:
            if isinstance(block, dict) and block.get("type") == "text":
                out_parts.append(str(block.get("text", "")))
        return "".join(out_parts)

    def chat_stream(self, messages: list[dict[str, Any]], **kwargs: Any) -> Iterator[str]:
        system_text, anthropic_msgs = self._to_anthropic_messages(messages)
        payload: dict[str, Any] = {
            "model": self._model,
            "messages": anthropic_msgs,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "stream": True,
        }
        if system_text:
            payload["system"] = system_text
        if "temperature" in kwargs:
            payload["temperature"] = kwargs["temperature"]
        yield from self._stream_openai_sse("/v1/messages", payload)


class FutureSyntexaProvider(SyntexaNativeLLMProvider):
    """
    Placeholder da IA proprietária Syntexa (próximos checkpoints treinados internamente).
    Mantém mesma interface para swap de runtime por env.
    """

    name: ProviderName = "future_syntexa"


class AzureOpenAIProvider(HTTPJSONLLMProvider):
    """
    Provedor Azure OpenAI (chat completions), usando endpoint compatível:
    {endpoint}/openai/deployments/{deployment}
    """

    def __init__(self, endpoint: str, api_key: str, deployment: str):
        base = endpoint.rstrip("/")
        if not base.endswith(f"/openai/deployments/{deployment}"):
            base = f"{base}/openai/deployments/{deployment}"
        super().__init__(name="azure_openai", base_url=base, api_key=api_key)

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["api-key"] = self.api_key
        return headers

    def chat(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        payload: dict[str, Any] = {
            "messages": messages,
        }
        if "temperature" in kwargs:
            payload["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            payload["max_tokens"] = kwargs["max_tokens"]
        # versão estável default
        api_ver = kwargs.get("api_version", "2024-10-21")
        _to = kwargs.get("timeout")
        if _to is None:
            _to = (
                float(getattr(settings, "llm_connect_timeout", 3.0)),
                float(getattr(settings, "llm_read_timeout", 120.0)),
            )
        resp = self._post_with_retry(
            f"/chat/completions?api-version={api_ver}",
            payload=payload,
            timeout=_to,
        )
        data = resp.json()
        choices = data.get("choices") or []
        if not choices:
            return ""
        message = choices[0].get("message") or {}
        return str(message.get("content", ""))

    def chat_stream(self, messages: list[dict[str, Any]], **kwargs: Any) -> Iterator[str]:
        payload: dict[str, Any] = {
            "messages": messages,
            "stream": True,
        }
        if "temperature" in kwargs:
            payload["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            payload["max_tokens"] = kwargs["max_tokens"]
        api_ver = kwargs.get("api_version", "2024-10-21")
        yield from self._stream_openai_sse(
            f"/chat/completions?api-version={api_ver}",
            payload,
        )


class LLMEngine:
    """
    Orquestra provedores de LLM (dummy, HTTP/vLLM, etc.).
    """

    def __init__(self, default_provider: ProviderName | None = None):
        self._providers: dict[ProviderName, LLMProvider] = {}
        self._provider_runtime_health: dict[str, float] = {}
        self._provider_runtime_failures: dict[str, int] = {}

        # ── MOTOR SOBERANO SOMENTE ───────────────────────────────
        # REMOVIDO: Todos os providers externos (OpenAI, Anthropic, Gemini,
        # DeepSeek, Azure, Ollama, vLLM, ExLlama, HTTP genérico).
        # A Syntexa opera EXCLUSIVAMENTE com a Foundation Model própria.
        # ─────────────────────────────────────────────────────────

        # Núcleo proprietário Syntexa Foundation Model.
        self.register_provider(SyntexaNativeLLMProvider())

        # Bridge transitório (Fase 1): permite Ollama (cloud ou self-hosted) coexistir
        # com o motor próprio enquanto a Foundation Model é treinada. Ativado SOMENTE
        # se OLLAMA_ENDPOINT estiver configurado no .env. Não substitui o syntexa_native.
        try:
            _ollama_ep = (getattr(settings, "ollama_endpoint", None) or "").strip()
            if _ollama_ep:
                _ollama_model = (getattr(settings, "ollama_model", None) or "llama3.2").strip()
                _ollama_key = (getattr(settings, "ollama_api_key", None) or "").strip() or None
                self.register_provider(
                    OllamaLLMProvider(
                        base_url=_ollama_ep,
                        model=_ollama_model,
                        api_key=_ollama_key,
                    )
                )
        except Exception as _exc:
            logger.warning("Falha ao registrar OllamaLLMProvider: %s", _exc)

        # Default: respeita DEFAULT_LLM se o provider foi registrado; senão, syntexa_native.
        configured_default = (default_provider or settings.default_llm or "").strip().lower()
        if configured_default in self._providers:
            self._default = configured_default
        else:
            self._default = "syntexa_native"

        # Verifica se o runtime da IA própria está pronto
        ok, reason = runtime_ready_for_active_model()
        if not ok:
            logger.warning(
                "[LLMEngine] Runtime da IA própria não está pronto: %s. "
                "Treine o modelo: python -m vereda_ai.syntexa_core.foundation_trainer_cli --data dataset.jsonl",
                reason,
            )

    def available_providers(self) -> list[str]:
        return sorted(self._providers.keys())

    def default_provider(self) -> str:
        return str(self._default)

    def _is_sovereign_provider(self, name: str) -> bool:
        return name in {"syntexa_native", "future_syntexa"}

    def _scoreboard_path(self) -> Path:
        raw = str(getattr(settings, "llm_quality_scoreboard_path", "") or "").strip()
        if not raw:
            raw = "config/llm_quality_scoreboard.json"
        path = Path(raw)
        if not path.is_absolute():
            path = Path(__file__).resolve().parents[2] / path
        return path

    def _load_scoreboard(self) -> dict[str, Any]:
        path = self._scoreboard_path()
        try:
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return data
        except Exception as exc:
            logger.warning("Falha ao ler placar de qualidade (%s): %s", path, exc)
        return {}

    def _domain_overrides(self) -> dict[str, str]:
        raw = str(getattr(settings, "llm_domain_provider_overrides", "") or "").strip()
        out: dict[str, str] = {}
        if not raw:
            return out
        for pair in raw.split(","):
            if "=" not in pair:
                continue
            k, v = pair.split("=", 1)
            dk = k.strip().lower()
            pv = v.strip().lower()
            if dk and pv:
                out[dk] = pv
        return out

    def _provider_confidence(self, provider_name: str, domain: str | None) -> float:
        base = 0.5
        board = self._load_scoreboard()
        providers = board.get("providers") if isinstance(board, dict) else None
        if isinstance(providers, dict):
            row = providers.get(provider_name) or {}
            if isinstance(row, dict):
                if isinstance(row.get("global_score"), (int, float)):
                    base = float(row["global_score"])
                domains = row.get("domains") or {}
                if domain and isinstance(domains, dict):
                    if isinstance(domains.get(domain), (int, float)):
                        base = float(domains[domain])
        rt = float(self._provider_runtime_health.get(provider_name, 0.0))
        fails = int(self._provider_runtime_failures.get(provider_name, 0))
        penalty = min(0.2, 0.03 * fails)
        return max(0.0, min(1.0, base * 0.75 + rt * 0.25 - penalty))

    def _mark_provider_ok(self, provider_name: str) -> None:
        prev = float(self._provider_runtime_health.get(provider_name, 0.6))
        self._provider_runtime_health[provider_name] = min(1.0, prev * 0.88 + 0.12)
        self._provider_runtime_failures[provider_name] = max(
            0, int(self._provider_runtime_failures.get(provider_name, 0)) - 1
        )

    def _mark_provider_fail(self, provider_name: str) -> None:
        prev = float(self._provider_runtime_health.get(provider_name, 0.6))
        self._provider_runtime_health[provider_name] = max(0.0, prev * 0.8)
        self._provider_runtime_failures[provider_name] = int(
            self._provider_runtime_failures.get(provider_name, 0)
        ) + 1

    def _candidate_provider_order(
        self,
        *,
        requested: str | None,
        domain: str | None,
        min_confidence: float,
    ) -> list[str]:
        """
        Ordem de prioridade (arquitetura soberana V37):
        1) Runtime local / soberano (syntexa_native, future_syntexa)
        2) Inferência local (ollama, local_http, exllama, vllm, tgi)
        3) Providers externos SOMENTE se external_providers_enabled=True e não soberano
        4) Dummy (sempre último recurso; levanta exceção)
        """
        sovereign_mode = bool(getattr(settings, "own_model_sovereign_mode", True))
        external_enabled = bool(getattr(settings, "external_providers_enabled", False))

        # Modo soberano: apenas providers próprios
        if sovereign_mode:
            if requested and self._is_sovereign_provider(requested):
                return [requested]
            if self._default in self._providers and self._is_sovereign_provider(self._default):
                return [self._default]
            sovereign = [x for x in self._providers.keys() if self._is_sovereign_provider(x)]
            return sovereign or ["syntexa_native"]

        if requested:
            return [requested]

        if not bool(getattr(settings, "llm_smart_fallback_enabled", True)):
            return [self._default]

        # Classificação de providers
        local_providers = {"syntexa_native", "future_syntexa", "ollama", "local_http", "exllama", "vllm", "azure_tgi"}
        external_providers = {"openai", "deepseek", "gemini", "anthropic", "azure_openai", "remote"}

        all_names = [name for name in self._providers.keys() if name != "dummy"]
        if not all_names:
            return [self._default]

        # Domain override respeita a classificação: se for local, vai primeiro; se for externo, só se permitido
        overrides = self._domain_overrides()
        if domain and overrides.get(domain) in self._providers:
            preferred = overrides[domain]
            tail = [x for x in all_names if x != preferred]
            # Se externo não permitido, move para depois dos locais
            if preferred in external_providers and not external_enabled:
                local_tail = [x for x in tail if x in local_providers]
                ext_tail = [x for x in tail if x in external_providers]
                return [*local_tail, preferred, *ext_tail]
            return [preferred, *tail]

        # Separa locais e externos
        locals_ordered: list[str] = []
        externals_ordered: list[str] = []
        for name in all_names:
            if name in local_providers:
                locals_ordered.append(name)
            elif name in external_providers:
                if external_enabled:
                    externals_ordered.append(name)
            else:
                # Provider desconhecido: assume local se não estiver na lista externa
                locals_ordered.append(name)

        # Ordena cada grupo por confiança/runtime health
        def _sort_by_confidence(names: list[str]) -> list[str]:
            scored = [(self._provider_confidence(n, domain), n) for n in names]
            scored.sort(reverse=True)
            return [n for _, n in scored if _ >= min_confidence] or [n for _, n in scored]

        locals_sorted = _sort_by_confidence(locals_ordered)
        externals_sorted = _sort_by_confidence(externals_ordered)

        # Garante que o default vá primeiro se for local; se for externo e não permitido, ignora
        default = self._default
        if default in locals_sorted:
            locals_sorted.remove(default)
            locals_sorted.insert(0, default)
        elif default in externals_sorted:
            if not external_enabled:
                externals_sorted.remove(default)
            else:
                externals_sorted.remove(default)
                externals_sorted.insert(0, default)

        result = [*locals_sorted, *externals_sorted]
        return result or [self._default]

    def register_provider(self, provider: LLMProvider) -> None:
        logger.info("Registrando provedor LLM: %s", provider.name)
        self._providers[provider.name] = provider

    def has_provider(self, name: str) -> bool:
        return name in self._providers

    def chat(
        self,
        messages: list[dict[str, Any]],
        provider: ProviderName | None = None,
        **kwargs: Any,
    ) -> str:
        timeout = kwargs.get("timeout", getattr(settings, "llm_chat_timeout", 120))
        kwargs.setdefault("timeout", timeout)
        soft_timeout = float(getattr(settings, "llm_soft_timeout", 300.0))
        domain = str(kwargs.pop("domain", "") or "").strip().lower() or None
        min_confidence = float(
            kwargs.pop(
                "min_confidence",
                getattr(settings, "llm_smart_fallback_min_confidence", 0.55),
            )
        )
        candidates = self._candidate_provider_order(
            requested=provider,
            domain=domain,
            min_confidence=max(0.0, min(1.0, min_confidence)),
        )
        last_exc: Exception | None = None
        for cand in candidates:
            prov = self._providers[cand]
            try:
                with ThreadPoolExecutor(max_workers=1) as ex:
                    fut = ex.submit(prov.chat, messages, **kwargs)
                    out = fut.result(timeout=max(1.0, soft_timeout))
                self._mark_provider_ok(cand)
                return out
            except FuturesTimeoutError:
                self._mark_provider_fail(cand)
                last_exc = TimeoutError(
                    f"Provedor LLM '{prov.name}' não respondeu em {soft_timeout}s."
                )
                logger.warning("LLM soft-timeout (%ss) no provedor %s", soft_timeout, prov.name)
            except (requests.RequestException, OSError, TimeoutError, RuntimeError) as e:
                self._mark_provider_fail(cand)
                last_exc = e
                logger.warning(
                    "LLM %s indisponível (%s). Erro: %s",
                    prov.name,
                    getattr(prov, "base_url", "?"),
                    e,
                )
                continue
        if last_exc:
            raise last_exc
        raise RuntimeError("Nenhum provedor LLM disponível para chat.")

    def chat_stream(
        self,
        messages: list[dict[str, Any]],
        provider: ProviderName | None = None,
        **kwargs: Any,
    ) -> Iterator[str]:
        """Stream de chunks para resposta imediata. Se o provedor não suportar, entrega a resposta inteira de uma vez."""
        timeout = kwargs.get("timeout", getattr(settings, "llm_chat_timeout", 10))
        kwargs.setdefault("timeout", timeout)
        domain = str(kwargs.pop("domain", "") or "").strip().lower() or None
        min_confidence = float(
            kwargs.pop(
                "min_confidence",
                getattr(settings, "llm_smart_fallback_min_confidence", 0.55),
            )
        )
        candidates = self._candidate_provider_order(
            requested=provider,
            domain=domain,
            min_confidence=max(0.0, min(1.0, min_confidence)),
        )
        last_exc: Exception | None = None
        for cand in candidates:
            prov = self._providers[cand]
            if hasattr(prov, "chat_stream"):
                try:
                    yielded_any = False
                    for piece in prov.chat_stream(messages, **kwargs):
                        yielded_any = True
                        yield piece
                    if yielded_any:
                        self._mark_provider_ok(cand)
                        return
                except (requests.RequestException, OSError, TimeoutError, RuntimeError) as e:
                    self._mark_provider_fail(cand)
                    last_exc = e
                    logger.warning("LLM stream falhou no provedor %s. Erro: %s", prov.name, e)
                    continue
            try:
                reply = self.chat(
                    messages,
                    provider=cand,
                    domain=domain,
                    min_confidence=min_confidence,
                    **kwargs,
                )
                if reply:
                    self._mark_provider_ok(cand)
                    yield reply
                    return
            except Exception as e:
                self._mark_provider_fail(cand)
                last_exc = e
                continue
        if last_exc:
            raise last_exc

    def embed(
        self,
        texts: list[str],
        provider: ProviderName | None = None,
        **kwargs: Any,
    ) -> list[list[float]]:
        prov = self._providers[provider or self._default]
        return prov.embed(texts, **kwargs)
