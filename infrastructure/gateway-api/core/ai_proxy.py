"""Proxy para workers de IA externos (Kaggle/GPU, servidor local, Ollama).

Não carrega nenhuma biblioteca de IA no import. Toda comunicação é via HTTP/httpx.
"""
from __future__ import annotations

import logging
import time
from typing import Any, AsyncGenerator

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from gateway.core.config import settings

logger = logging.getLogger(__name__)

# Cliente compartilhado (async) para evitar overhead de conexão
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
    if settings.ai_worker_url and endpoint_url.startswith(settings.ai_worker_url) and settings.ai_worker_api_key:
        headers["Authorization"] = f"Bearer {settings.ai_worker_api_key}"
    if settings.local_ai_url and endpoint_url.startswith(settings.local_ai_url) and settings.local_ai_api_key:
        headers["Authorization"] = f"Bearer {settings.local_ai_api_key}"
    return headers


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
def proxy_to_ai_worker_sync(
    path: str,
    payload: dict[str, Any],
    *,
    timeout_sec: float = 120.0,
) -> dict[str, Any]:
    """Chamada síncrona para o AI Worker (Kaggle/GPU)."""
    url = (settings.ai_worker_url or "").rstrip("/")
    if not url:
        raise RuntimeError("AI_WORKER_URL não configurado")
    client = _get_sync_client()
    target = f"{url}/{path.lstrip('/')}"
    try:
        resp = client.post(
            target,
            json=payload,
            headers=_headers_for(url),
            timeout=timeout_sec,
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as exc:
        logger.warning("AI Worker HTTP %s: %s", exc.response.status_code, exc.response.text[:200])
        raise
    except Exception as exc:
        logger.warning("AI Worker falhou: %s", exc)
        raise


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
async def proxy_to_ai_worker_async(
    path: str,
    payload: dict[str, Any],
    *,
    timeout_sec: float = 120.0,
) -> dict[str, Any]:
    """Chamada assíncrona para o AI Worker (Kaggle/GPU)."""
    url = (settings.ai_worker_url or "").rstrip("/")
    if not url:
        raise RuntimeError("AI_WORKER_URL não configurado")
    client = _get_async_client()
    target = f"{url}/{path.lstrip('/')}"
    try:
        resp = await client.post(
            target,
            json=payload,
            headers=_headers_for(url),
            timeout=timeout_sec,
        )
        resp.raise_for_status()
        return resp.json()
    except httpx.HTTPStatusError as exc:
        logger.warning("AI Worker HTTP %s: %s", exc.response.status_code, exc.response.text[:200])
        raise
    except Exception as exc:
        logger.warning("AI Worker falhou: %s", exc)
        raise


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=5), reraise=True)
def proxy_to_local_ai_sync(
    path: str,
    payload: dict[str, Any],
    *,
    timeout_sec: float = 120.0,
) -> dict[str, Any]:
    """Chamada síncrona para o servidor local privado (Ollama/pipelines sigilosos)."""
    url = (settings.local_ai_url or "").rstrip("/")
    if not url:
        raise RuntimeError("LOCAL_AI_URL não configurado")
    client = _get_sync_client()
    target = f"{url}/{path.lstrip('/')}"
    try:
        resp = client.post(
            target,
            json=payload,
            headers=_headers_for(url),
            timeout=timeout_sec,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Local AI falhou: %s", exc)
        raise


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=5), reraise=True)
async def proxy_to_local_ai_async(
    path: str,
    payload: dict[str, Any],
    *,
    timeout_sec: float = 120.0,
) -> dict[str, Any]:
    """Chamada assíncrona para o servidor local privado."""
    url = (settings.local_ai_url or "").rstrip("/")
    if not url:
        raise RuntimeError("LOCAL_AI_URL não configurado")
    client = _get_async_client()
    target = f"{url}/{path.lstrip('/')}"
    try:
        resp = await client.post(
            target,
            json=payload,
            headers=_headers_for(url),
            timeout=timeout_sec,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as exc:
        logger.warning("Local AI falhou: %s", exc)
        raise


def proxy_chat_completion_sync(
    messages: list[dict[str, str]],
    model: str | None = None,
    stream: bool = False,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> dict[str, Any]:
    """Roteia chat completion para o worker apropriado."""
    payload = {
        "messages": messages,
        "model": model or "default",
        "stream": stream,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    # Prioridade: Local -> AI Worker
    if settings.local_ai_url:
        try:
            return proxy_to_local_ai_sync("/v1/chat/completions", payload, timeout_sec=120.0)
        except Exception:
            pass
    return proxy_to_ai_worker_sync("/v1/chat/completions", payload, timeout_sec=120.0)


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
    if settings.local_ai_url:
        try:
            return await proxy_to_local_ai_async("/v1/chat/completions", payload, timeout_sec=120.0)
        except Exception:
            pass
    return await proxy_to_ai_worker_async("/v1/chat/completions", payload, timeout_sec=120.0)


def proxy_embeddings_sync(texts: list[str], model: str | None = None) -> dict[str, Any]:
    payload = {"texts": texts, "model": model or "default"}
    return proxy_to_ai_worker_sync("/v1/embeddings", payload, timeout_sec=60.0)


async def proxy_embeddings_async(texts: list[str], model: str | None = None) -> dict[str, Any]:
    payload = {"texts": texts, "model": model or "default"}
    return await proxy_to_ai_worker_async("/v1/embeddings", payload, timeout_sec=60.0)


def proxy_rerank_sync(query: str, documents: list[str], model: str | None = None) -> dict[str, Any]:
    payload = {"query": query, "documents": documents, "model": model or "default"}
    return proxy_to_ai_worker_sync("/v1/rerank", payload, timeout_sec=60.0)


async def proxy_rerank_async(query: str, documents: list[str], model: str | None = None) -> dict[str, Any]:
    payload = {"query": query, "documents": documents, "model": model or "default"}
    return await proxy_to_ai_worker_async("/v1/rerank", payload, timeout_sec=60.0)
