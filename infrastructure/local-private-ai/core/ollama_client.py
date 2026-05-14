"""Cliente HTTP para Ollama — não depende de bibliotecas pesadas."""
from __future__ import annotations

import logging
from typing import Any

import httpx

from local_private_ai.core.config import settings

logger = logging.getLogger(__name__)

_httpx_client: httpx.Client | None = None


def _get_client() -> httpx.Client:
    global _httpx_client
    if _httpx_client is None:
        _httpx_client = httpx.Client(
            timeout=httpx.Timeout(connect=5.0, read=300.0, write=30.0, pool=5.0),
        )
    return _httpx_client


def _headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if settings.ollama_api_key:
        headers["Authorization"] = f"Bearer {settings.ollama_api_key}"
    return headers


def ollama_chat(messages: list[dict[str, str]], model: str | None = None, stream: bool = False) -> dict[str, Any]:
    url = f"{settings.ollama_endpoint.rstrip('/')}/api/chat"
    payload = {
        "model": model or settings.ollama_default_model,
        "messages": messages,
        "stream": stream,
    }
    resp = _get_client().post(url, json=payload, headers=_headers())
    resp.raise_for_status()
    return resp.json()


def ollama_generate(prompt: str, model: str | None = None, stream: bool = False) -> dict[str, Any]:
    url = f"{settings.ollama_endpoint.rstrip('/')}/api/generate"
    payload = {
        "model": model or settings.ollama_default_model,
        "prompt": prompt,
        "stream": stream,
    }
    resp = _get_client().post(url, json=payload, headers=_headers())
    resp.raise_for_status()
    return resp.json()


def ollama_embeddings(texts: list[str], model: str | None = None) -> dict[str, Any]:
    url = f"{settings.ollama_endpoint.rstrip('/')}/api/embed"
    payload = {
        "model": model or settings.ollama_default_model,
        "input": texts,
    }
    resp = _get_client().post(url, json=payload, headers=_headers())
    resp.raise_for_status()
    return resp.json()
