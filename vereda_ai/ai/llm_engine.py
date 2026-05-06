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
    name: ProviderName = "dummy"

    def chat(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        # Importante: o Dummy é apenas fallback/dev. Não deve "ecoar" a pergunta,
        # porque isso parece bug para o usuário e mascara falta de configuração.
        #
        # Para ter respostas completas, configure DEFAULT_LLM=syntexa_native (padrão)
        # ou um endpoint HTTP próprio (LOCAL_LLM_ENDPOINT, EXLLAMA_ENDPOINT, etc.).
        # Veja `.env.example` na raiz do projeto.
        has_any_user = any((m.get("role") or "").lower() == "user" for m in messages)
        if not has_any_user:
            return "Olá! Sou a Syntexa. Envie sua pergunta para começarmos."
        return (
            "O núcleo de geração da Syntexa está indisponível neste momento. "
            "Tente novamente em instantes."
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
        from vereda_ai.syntexa_core.hybrid_engine import generate_reply

        return generate_reply(messages)

    def chat_stream(self, messages: list[dict[str, Any]], **kwargs: Any) -> Iterator[str]:
        from vereda_ai.syntexa_core.hybrid_engine import generate_reply_stream

        yield from generate_reply_stream(messages)

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
        sovereign_mode = bool(getattr(settings, "own_model_sovereign_mode", True))
        strict_no_fallback = bool(getattr(settings, "own_model_strict_no_fallback", False))
        prefer_external_if_configured = bool(
            getattr(settings, "prefer_external_llm_when_configured", False)
        )

        # Registra dummy apenas como "último recurso" fora de produção.
        # Em produção, a intenção é usar provedores reais (HTTP próprio / Azure / etc.) sem fallback sintético.
        dummy = DummyLLMProvider()

        # Núcleo proprietário Syntexa (sempre disponível — não depende de endpoints externos).
        self.register_provider(SyntexaNativeLLMProvider())

        # Ollama (local :11434 ou cloud): gera texto; embeddings/RAG seguem no núcleo nativo dentro de OllamaLLMProvider.
        if (not sovereign_mode) and getattr(settings, "ollama_endpoint", None):
            _om = (getattr(settings, "ollama_model", None) or "llama3.2").strip()
            self.register_provider(
                OllamaLLMProvider(
                    base_url=str(settings.ollama_endpoint).strip(),
                    model=_om,
                    api_key=getattr(settings, "ollama_api_key", None),
                )
            )

        # Opcional: servidor HTTP local/externo compatível com OpenAI/vLLM.
        if (not sovereign_mode) and settings.local_llm_endpoint:
            http_provider = HTTPJSONLLMProvider(
                name="local_http", base_url=settings.local_llm_endpoint
            )
            self.register_provider(http_provider)
        if (not sovereign_mode) and getattr(settings, "openai_endpoint", None) and getattr(settings, "openai_api_key", None):
            self.register_provider(
                OpenAIProvider(
                    base_url=getattr(settings, "openai_endpoint"),
                    api_key=getattr(settings, "openai_api_key"),
                    model=getattr(settings, "openai_model", None) or "gpt-4o-mini",
                )
            )
        self.register_provider(FutureSyntexaProvider())

        # ExLlama (gateway HTTP) — registra como 'exllama' quando configurado
        if (not sovereign_mode) and getattr(settings, "exllama_endpoint", None):
            exll = HTTPJSONLLMProvider(
                name="exllama", base_url=getattr(settings, "exllama_endpoint")
            )
            self.register_provider(exll)
        # Azure TGI / Remote HTTP providers
        if (not sovereign_mode) and getattr(settings, "azure_tgi_endpoint", None):
            tgi = HTTPJSONLLMProvider(
                name="azure_tgi", base_url=getattr(settings, "azure_tgi_endpoint")
            )
            self.register_provider(tgi)
        if (
            (not sovereign_mode)
            and
            getattr(settings, "azure_openai_endpoint", None)
            and getattr(settings, "azure_openai_key", None)
            and getattr(settings, "azure_openai_deployment", None)
        ):
            ao = AzureOpenAIProvider(
                endpoint=getattr(settings, "azure_openai_endpoint"),
                api_key=getattr(settings, "azure_openai_key"),
                deployment=getattr(settings, "azure_openai_deployment"),
            )
            self.register_provider(ao)
        if (not sovereign_mode) and getattr(settings, "remote_llm_endpoint", None):
            remote = HTTPJSONLLMProvider(
                name="remote", base_url=getattr(settings, "remote_llm_endpoint")
            )
            self.register_provider(remote)

        # Produção: DEFAULT_LLM=syntexa_native OU endpoint de inferência próprio na Azure/VM.
        env = (getattr(settings, "environment", "") or "").strip().lower()
        is_prod = env in {"prod", "production"}
        if is_prod:
            any_external = any(
                getattr(settings, k, None)
                for k in (
                    "ollama_endpoint",
                    "exllama_endpoint",
                    "local_llm_endpoint",
                    "azure_tgi_endpoint",
                    "azure_openai_endpoint",
                    "remote_llm_endpoint",
                )
            )
            dl = (default_provider or settings.default_llm or "").strip().lower()
            if (not sovereign_mode) and (not any_external) and dl not in ("syntexa_native",):
                raise RuntimeError(
                    "Produção: use DEFAULT_LLM=syntexa_native (motor proprietário) ou configure um endpoint "
                    "de inferência (OLLAMA_ENDPOINT, EXLLAMA_ENDPOINT, LOCAL_LLM_ENDPOINT, …)."
                )

        # Respeita DEFAULT_LLM; syntexa_native usa contexto da web + lógica interna (sem roubar para Azure).
        configured_default = (default_provider or settings.default_llm or dummy.name).strip().lower()
        if (not sovereign_mode) and is_prod and configured_default not in self._providers and configured_default != "dummy":
            raise RuntimeError(
                f"Produção: DEFAULT_LLM='{configured_default}' não está disponível no runtime. "
                "Verifique endpoint/credenciais e variáveis de ambiente."
            )
        if configured_default in self._providers and configured_default != "dummy":
            self._default = configured_default
        elif configured_default == "syntexa_native" or (settings.default_llm or "").strip().lower() == "syntexa_native":
            self._default = "syntexa_native"
        elif "azure_openai" in self._providers:
            self._default = "azure_openai"
        elif "azure_tgi" in self._providers:
            self._default = "azure_tgi"
        elif "exllama" in self._providers:
            self._default = "exllama"
        elif "ollama" in self._providers:
            self._default = "ollama"
        elif "openai" in self._providers:
            self._default = "openai"
        elif "local_http" in self._providers:
            self._default = "local_http"
        elif "syntexa_native" in self._providers:
            self._default = "syntexa_native"
        elif configured_default in self._providers:
            self._default = configured_default
        else:
            self.register_provider(dummy)
            self._default = dummy.name

        # Modo soberano: quando estrito, força o núcleo proprietário como motor textual primário,
        # mesmo que haja endpoints externos configurados no ambiente.
        if strict_no_fallback and "syntexa_native" in self._providers:
            self._default = "syntexa_native"

        # -----------------------------------------------------------------
        # Motor textual principal (causa raiz de respostas “quebradas”):
        # O default histórico DEFAULT_LLM=syntexa_native activa o hybrid_engine
        # (regras + síntese de web), não o modelo Ollama/HTTP — mesmo com OLLAMA_ENDPOINT
        # configurado. Aqui: se o utilizador deixou o default “native” mas há API de
        # chat real registada, essa API passa a ser o _default. syntexa_native continua
        # registado (embeddings/RAG); não é cadeia de fallback em tempo de execução.
        # -----------------------------------------------------------------
        if (
            prefer_external_if_configured
            and self._default == "syntexa_native"
            and not (strict_no_fallback or is_prod)
        ):
            for _name in (
                "ollama",
                "local_http",
                "openai",
                "azure_openai",
                "azure_tgi",
                "exllama",
                "remote",
            ):
                if _name in self._providers:
                    self._default = _name
                    logger.info(
                        "Chat: motor textual = %s (API LLM). syntexa_native não é o primário "
                        "enquanto este endpoint estiver configurado.",
                        _name,
                    )
                    break

        if self._default == "syntexa_native" and (strict_no_fallback or is_prod):
            ok, reason = runtime_ready_for_active_model()
            if not ok:
                raise RuntimeError(
                    "Modo estrito sem fallback ativado: runtime da IA própria não está pronto. "
                    f"Detalhe: {reason}"
                )
        if sovereign_mode:
            self._default = "syntexa_native"

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
        sovereign_mode = bool(getattr(settings, "own_model_sovereign_mode", True))
        if sovereign_mode:
            if requested and self._is_sovereign_provider(requested):
                return [requested]
            if self._default in self._providers and self._is_sovereign_provider(self._default):
                return [self._default]
            return [x for x in self._providers.keys() if self._is_sovereign_provider(x)] or ["syntexa_native"]
        if requested:
            return [requested]
        if not bool(getattr(settings, "llm_smart_fallback_enabled", True)):
            return [self._default]
        all_names = [name for name in self._providers.keys() if name != "dummy"]
        if not all_names:
            return [self._default]
        overrides = self._domain_overrides()
        if domain and overrides.get(domain) in self._providers:
            preferred = overrides[domain]
            tail = [x for x in all_names if x != preferred]
            return [preferred, *tail]
        scored: list[tuple[float, str]] = []
        for name in all_names:
            scored.append((self._provider_confidence(name, domain), name))
        scored.sort(reverse=True)
        filtered = [name for score, name in scored if score >= min_confidence]
        if self._default in all_names and self._default not in filtered:
            filtered.insert(0, self._default)
        if not filtered:
            filtered = [name for _, name in scored]
        return filtered or [self._default]

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
