from typing import Any, Iterator, Protocol
import threading
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

import requests

from vereda_ai.core.config import settings
from vereda_ai.core.logging import get_logger


ProviderName = str

logger = get_logger(__name__)
_LLM_SEMAPHORE = threading.BoundedSemaphore(
    max(1, int(getattr(settings, "llm_max_concurrency", 4)))
)
_SOFT_FALLBACK_TEXT = "Resposta gerada pelo motor local da Syntexa."  # usado apenas pelo DummyLLMProvider


class LLMProvider(Protocol):
    name: ProviderName

    def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        ...

    def embed(self, texts: list[str], **kwargs: Any) -> list[list[float]]:
        ...


class DummyLLMProvider:
    name: ProviderName = "dummy"

    def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        # Importante: o Dummy é apenas fallback/dev. Não deve "ecoar" a pergunta,
        # porque isso parece bug para o usuário e mascara falta de configuração.
        #
        # Para ter respostas completas, configure um provedor real:
        # - OLLAMA_ENDPOINT e DEFAULT_LLM=ollama (recomendado)
        # - ou LOCAL_LLM_ENDPOINT e DEFAULT_LLM=local_http
        #
        # Veja `.env.example` na raiz do projeto.
        has_any_user = any((m.get("role") or "").lower() == "user" for m in messages)
        if not has_any_user:
            return "Olá! Sou a Syntexa. Envie sua pergunta para começarmos."
        return (
            "O provedor de IA não está configurado neste ambiente. "
            "Configure `OLLAMA_ENDPOINT` e `DEFAULT_LLM=ollama` (ou `LOCAL_LLM_ENDPOINT`). "
            "Exemplo em `.env.example`."
        )

    def embed(self, texts: list[str], **kwargs: Any) -> list[list[float]]:
        return [[float(len(t))] for t in texts]


class OllamaLLMProvider:
    """
    Provedor para Ollama em /api/generate.
    """

    def __init__(self, name: ProviderName, base_url: str, model: str = "mistral"):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.model = model

    def _resolve_model(self, requested_model: str | None) -> str:
        # Evita enviar nomes internos do app (ex: vereda-small-echo) ao Ollama.
        if not requested_model:
            return self.model
        m = str(requested_model).strip()
        if not m or m.startswith("vereda-"):
            return self.model
        return m

    @staticmethod
    def _messages_to_prompt(messages: list[dict[str, str]]) -> str:
        parts: list[str] = []
        for m in messages:
            role = (m.get("role") or "user").upper()
            content = m.get("content") or ""
            parts.append(f"{role}: {content}")
        parts.append("ASSISTANT:")
        return "\n".join(parts)

    def _post_with_retry(
        self,
        url: str,
        *,
        json_payload: dict[str, Any],
        stream: bool = False,
        timeout: float | tuple[float, float] | None = None,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        attempts = max(1, int(getattr(settings, "llm_retry_count", 3)))
        backoff_ms = max(0, int(getattr(settings, "llm_retry_backoff_ms", 150)))
        connect_timeout = float(getattr(settings, "llm_connect_timeout", 3.0))
        read_timeout = float(getattr(settings, "llm_read_timeout", 120.0))
        req_timeout = timeout if timeout is not None else (connect_timeout, read_timeout)
        last_exc: Exception | None = None
        for i in range(attempts):
            try:
                with _LLM_SEMAPHORE:
                    resp = requests.post(
                        url,
                        json=json_payload,
                        headers=headers or {"Content-Type": "application/json"},
                        timeout=req_timeout,
                        stream=stream,
                    )
                resp.raise_for_status()
                return resp
            except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as exc:
                last_exc = exc
                logger.warning(
                    "Falha ao chamar Ollama (tentativa %s/%s): %s",
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

    def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        resolved_model = self._resolve_model(kwargs.get("model"))
        payload: dict[str, Any] = {
            "model": resolved_model,
            "prompt": self._messages_to_prompt(messages),
            "stream": False,
        }
        if "temperature" in kwargs:
            payload["options"] = {"temperature": kwargs["temperature"]}
        if "max_tokens" in kwargs:
            payload.setdefault("options", {})["num_predict"] = kwargs["max_tokens"]
        payload.setdefault("options", {})["num_ctx"] = 4096

        req_timeout = kwargs.get("timeout", getattr(settings, "llm_chat_timeout", 10))
        resp = self._post_with_retry(
            f"{self.base_url}/api/generate",
            json_payload=payload,
            stream=False,
            timeout=req_timeout,
            headers={"Content-Type": "application/json"},
        )
        data = resp.json()
        return str(data.get("response", ""))

    def chat_stream(
        self, messages: list[dict[str, str]], **kwargs: Any
    ) -> Iterator[str]:
        """Gera chunks de texto para resposta imediata (streaming)."""
        resolved_model = self._resolve_model(kwargs.get("model"))
        payload: dict[str, Any] = {
            "model": resolved_model,
            "prompt": self._messages_to_prompt(messages),
            "stream": True,
        }
        if "temperature" in kwargs:
            payload.setdefault("options", {})["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            payload.setdefault("options", {})["num_predict"] = kwargs["max_tokens"]
        req_timeout = kwargs.get("timeout", getattr(settings, "llm_chat_timeout", 10))
        resp = self._post_with_retry(
            f"{self.base_url}/api/generate",
            json_payload=payload,
            stream=True,
            timeout=req_timeout,
            headers={"Content-Type": "application/json"},
        )
        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            try:
                import json as _json
                data = _json.loads(line)
                content = data.get("response") or ""
                if content:
                    yield content
                if data.get("done"):
                    break
            except Exception:
                continue

    def embed(self, texts: list[str], **kwargs: Any) -> list[list[float]]:
        # Ollama embeddings: POST /api/embeddings, model + prompt
        out = []
        for t in texts:
            r = self._post_with_retry(
                f"{self.base_url}/api/embeddings",
                json_payload={"model": self.model, "prompt": t},
                stream=False,
                timeout=kwargs.get("timeout", 30),
            )
            out.append(r.json().get("embedding", []))
        return out


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

    def chat(self, messages: list[dict[str, str]], **kwargs: Any) -> str:
        payload: dict[str, Any] = {
            "model": kwargs.get("model", "syntexa-large"),
            "messages": messages,
        }
        if "temperature" in kwargs:
            payload["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            payload["max_tokens"] = kwargs["max_tokens"]

        resp = self._post_with_retry(
            "/v1/chat/completions",
            payload=payload,
            timeout=kwargs.get("timeout", getattr(settings, "llm_chat_timeout", 10)),
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


class LLMEngine:
    """
    Orquestra provedores de LLM (dummy, HTTP/vLLM, etc.).
    """

    def __init__(self, default_provider: ProviderName | None = None):
        self._providers: dict[ProviderName, LLMProvider] = {}

        # Sempre registra dummy para ambiente de desenvolvimento.
        dummy = DummyLLMProvider()
        self.register_provider(dummy)

        # Ollama (Mistral, Llama, etc.) — prioridade se configurado.
        if settings.ollama_endpoint:
            ollama = OllamaLLMProvider(
                name="ollama",
                base_url=settings.ollama_endpoint,
                model=settings.ollama_model,
            )
            self.register_provider(ollama)

        # Opcional: servidor HTTP local/externo compatível com OpenAI/vLLM.
        if settings.local_llm_endpoint:
            http_provider = HTTPJSONLLMProvider(
                name="local_http", base_url=settings.local_llm_endpoint
            )
            self.register_provider(http_provider)

        # Escolhe default a partir das configs.
        # Se config vier como "dummy", mas houver provedor real disponível,
        # prioriza provedor real para evitar respostas de fallback.
        configured_default = (default_provider or settings.default_llm or dummy.name).strip()
        if configured_default in self._providers and configured_default != "dummy":
            self._default = configured_default
        elif "ollama" in self._providers:
            self._default = "ollama"
        elif "local_http" in self._providers:
            self._default = "local_http"
        elif configured_default in self._providers:
            self._default = configured_default
        else:
            self._default = dummy.name

    def register_provider(self, provider: LLMProvider) -> None:
        logger.info("Registrando provedor LLM: %s", provider.name)
        self._providers[provider.name] = provider

    def chat(
        self,
        messages: list[dict[str, str]],
        provider: ProviderName | None = None,
        **kwargs: Any,
    ) -> str:
        prov = self._providers[provider or self._default]
        timeout = kwargs.get("timeout", getattr(settings, "llm_chat_timeout", 120))
        kwargs.setdefault("timeout", timeout)
        soft_timeout = float(getattr(settings, "llm_soft_timeout", 20.0))
        try:
            with ThreadPoolExecutor(max_workers=1) as ex:
                fut = ex.submit(prov.chat, messages, **kwargs)
                return fut.result(timeout=max(1.0, soft_timeout))
        except FuturesTimeoutError:
            logger.warning("LLM soft-timeout (%ss) no provedor %s", soft_timeout, prov.name)
            raise TimeoutError(
                f"Provedor LLM '{prov.name}' não respondeu em {soft_timeout}s."
            )
        except (requests.RequestException, OSError) as e:
            logger.warning(
                "LLM %s indisponível (%s). Erro: %s",
                prov.name,
                getattr(prov, "base_url", "?"),
                e,
            )
            raise

    def chat_stream(
        self,
        messages: list[dict[str, str]],
        provider: ProviderName | None = None,
        **kwargs: Any,
    ) -> Iterator[str]:
        """Stream de chunks para resposta imediata. Se o provedor não suportar, entrega a resposta inteira de uma vez."""
        prov = self._providers[provider or self._default]
        timeout = kwargs.get("timeout", getattr(settings, "llm_chat_timeout", 10))
        kwargs.setdefault("timeout", timeout)
        if hasattr(prov, "chat_stream"):
            try:
                yield from prov.chat_stream(messages, **kwargs)
                return
            except (requests.RequestException, OSError) as e:
                logger.warning("LLM stream falhou no provedor %s. Erro: %s", prov.name, e)
                raise
        reply = self.chat(messages, provider=provider, **kwargs)
        if reply:
            yield reply

    def embed(
        self,
        texts: list[str],
        provider: ProviderName | None = None,
        **kwargs: Any,
    ) -> list[list[float]]:
        prov = self._providers[provider or self._default]
        return prov.embed(texts, **kwargs)
