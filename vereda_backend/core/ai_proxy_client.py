"""Cliente HTTP para proxy de IA — conecta Railway gateway a Local AI / Kaggle Workers.

Não carrega bibliotecas de IA. Comunicação puramente via HTTP/httpx.
Suporta múltiplos providers com failover automático:
  1. Local GPU
  2. Kaggle Worker 1
  3. Kaggle Worker 2
"""
from __future__ import annotations

import logging
from typing import Any

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from vereda_backend.core.config import settings

logger = logging.getLogger(__name__)

_httpx_async_client: httpx.AsyncClient | None = None
_httpx_sync_client: httpx.Client | None = None


def _get_sync_client() -> httpx.Client:
    global _httpx_sync_client
    if _httpx_sync_client is None:
        _httpx_sync_client = httpx.Client(
            timeout=httpx.Timeout(connect=5.0, read=120.0, write=30.0, pool=5.0),
            limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
        )
    return _httpx_sync_client


def _get_async_client() -> httpx.AsyncClient:
    global _httpx_async_client
    if _httpx_async_client is None:
        _httpx_async_client = httpx.AsyncClient(
            timeout=httpx.Timeout(connect=5.0, read=120.0, write=30.0, pool=5.0),
            limits=httpx.Limits(max_connections=50, max_keepalive_connections=20),
        )
    return _httpx_async_client


def _headers_for(endpoint_url: str) -> dict[str, str]:
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    ai_url = getattr(settings, "ai_worker_url", None) or ""
    ai_key = getattr(settings, "ai_worker_api_key", None) or ""
    local_url = getattr(settings, "local_ai_url", None) or ""
    local_key = getattr(settings, "local_ai_api_key", None) or ""
    if ai_url and endpoint_url.startswith(ai_url) and ai_key:
        headers["Authorization"] = f"Bearer {ai_key}"
    if local_url and endpoint_url.startswith(local_url) and local_key:
        headers["Authorization"] = f"Bearer {local_key}"
    return headers


def _kaggle_urls() -> list[str]:
    """Retorna lista de URLs Kaggle configuradas (Worker 1 e Worker 2)."""
    urls = []
    kw1 = (getattr(settings, "kaggle_inference_url_1", None) or "").strip()
    kw2 = (getattr(settings, "kaggle_inference_url_2", None) or "").strip()
    if kw1:
        urls.append(kw1)
    if kw2:
        urls.append(kw2)
    return urls


def _all_ai_urls() -> list[str]:
    """Retorna todos os providers na ordem de prioridade: Local > Kaggle1 > Kaggle2."""
    urls = []
    local = (getattr(settings, "local_ai_url", None) or "").strip()
    if local:
        urls.append(("local", local))
    for i, ku in enumerate(_kaggle_urls(), 1):
        urls.append((f"kaggle_{i}", ku))
    return urls


def _try_providers_sync(path: str, payload: dict[str, Any], timeout_sec: float) -> dict[str, Any]:
    """Tenta cada provider em ordem até um funcionar."""
    client = _get_sync_client()
    last_error = None
    for name, url in _all_ai_urls():
        target = f"{url.rstrip('/')}/{path.lstrip('/')}"
        try:
            resp = client.post(target, json=payload, headers=_headers_for(url), timeout=timeout_sec)
            resp.raise_for_status()
            logger.info("AI provider %s responded OK", name)
            return resp.json()
        except Exception as exc:
            logger.warning("AI provider %s failed: %s", name, exc)
            last_error = exc
    if last_error:
        raise last_error
    raise RuntimeError("Nenhum AI provider configurado ou disponível")


async def _try_providers_async(path: str, payload: dict[str, Any], timeout_sec: float) -> dict[str, Any]:
    """Tenta cada provider em ordem até um funcionar (async)."""
    client = _get_async_client()
    last_error = None
    for name, url in _all_ai_urls():
        target = f"{url.rstrip('/')}/{path.lstrip('/')}"
        try:
            resp = await client.post(target, json=payload, headers=_headers_for(url), timeout=timeout_sec)
            resp.raise_for_status()
            logger.info("AI provider %s responded OK", name)
            return resp.json()
        except Exception as exc:
            logger.warning("AI provider %s failed: %s", name, exc)
            last_error = exc
    if last_error:
        raise last_error
    raise RuntimeError("Nenhum AI provider configurado ou disponível")


# ── Funções legadas para compatibilidade ──
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
def proxy_to_ai_worker_sync(
    path: str,
    payload: dict[str, Any],
    *,
    timeout_sec: float = 120.0,
) -> dict[str, Any]:
    return _try_providers_sync(path, payload, timeout_sec)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
async def proxy_to_ai_worker_async(
    path: str,
    payload: dict[str, Any],
    *,
    timeout_sec: float = 120.0,
) -> dict[str, Any]:
    return await _try_providers_async(path, payload, timeout_sec)


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=5), reraise=True)
def proxy_to_local_ai_sync(
    path: str,
    payload: dict[str, Any],
    *,
    timeout_sec: float = 120.0,
) -> dict[str, Any]:
    url = (getattr(settings, "local_ai_url", None) or "").rstrip("/")
    if not url:
        raise RuntimeError("local_ai_url não configurado")
    client = _get_sync_client()
    target = f"{url}/{path.lstrip('/')}"
    resp = client.post(target, json=payload, headers=_headers_for(url), timeout=timeout_sec)
    resp.raise_for_status()
    return resp.json()


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=5), reraise=True)
async def proxy_to_local_ai_async(
    path: str,
    payload: dict[str, Any],
    *,
    timeout_sec: float = 120.0,
) -> dict[str, Any]:
    url = (getattr(settings, "local_ai_url", None) or "").rstrip("/")
    if not url:
        raise RuntimeError("local_ai_url não configurado")
    client = _get_async_client()
    target = f"{url}/{path.lstrip('/')}"
    resp = await client.post(target, json=payload, headers=_headers_for(url), timeout=timeout_sec)
    resp.raise_for_status()
    return resp.json()


def proxy_chat_completion_sync(
    messages: list[dict[str, str]],
    model: str | None = None,
    stream: bool = False,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> dict[str, Any]:
    payload = {
        "messages": messages,
        "model": model or "default",
        "stream": stream,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    return _try_providers_sync("/v1/chat/completions", payload, timeout_sec=120.0)


async def proxy_chat_completion_async(
    messages: list[dict[str, str]],
    model: str | None = None,
    stream: bool = False,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> dict[str, Any]:
    payload = {
        "messages": messages,
        "model": model or "default",
        "stream": stream,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    return await _try_providers_async("/v1/chat/completions", payload, timeout_sec=120.0)


def proxy_embeddings_sync(texts: list[str], model: str | None = None) -> dict[str, Any]:
    payload = {"texts": texts, "model": model or "default"}
    return _try_providers_sync("/v1/embeddings", payload, timeout_sec=60.0)


async def proxy_embeddings_async(texts: list[str], model: str | None = None) -> dict[str, Any]:
    payload = {"texts": texts, "model": model or "default"}
    return await _try_providers_async("/v1/embeddings", payload, timeout_sec=60.0)


def proxy_rerank_sync(query: str, documents: list[str], model: str | None = None) -> dict[str, Any]:
    payload = {"query": query, "documents": documents, "model": model or "default"}
    return _try_providers_sync("/v1/rerank", payload, timeout_sec=60.0)


async def proxy_rerank_async(query: str, documents: list[str], model: str | None = None) -> dict[str, Any]:
    payload = {"query": query, "documents": documents, "model": model or "default"}
    return await _try_providers_async("/v1/rerank", payload, timeout_sec=60.0)
