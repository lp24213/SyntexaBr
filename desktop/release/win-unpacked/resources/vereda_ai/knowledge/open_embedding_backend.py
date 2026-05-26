# -*- coding: utf-8 -*-
"""
Embeddings open-source para RAG e memória: Ollama `/api/embed`, FastEmbed (ONNX),
API `/v1/embeddings` compatível com OpenAI, e fallback hash (legado).
"""
from __future__ import annotations

import hashlib
import math
from typing import Any

import requests

from vereda_ai.core.config import settings
from vereda_ai.core.logging import get_logger

logger = get_logger(__name__)

_fastembed_model: Any = None
_fastembed_model_name: str | None = None


def hash_embed_texts(texts: list[str], dim: int = 64) -> list[list[float]]:
    """Vetores determinísticos (legado) — use só quando não há modelo real."""
    out: list[list[float]] = []
    for t in texts:
        h = hashlib.sha256((t or "").encode("utf-8")).digest()
        vec: list[float] = []
        for i in range(dim):
            b0 = h[i % len(h)]
            b1 = h[(i + 13) % len(h)]
            vec.append(math.sin((b0 + b1 * 256) / 1024.0))
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        out.append([x / norm for x in vec])
    return out


def embed_ollama(
    base_url: str,
    model: str,
    texts: list[str],
    *,
    timeout: float = 120.0,
) -> list[list[float]]:
    url = f"{base_url.rstrip('/')}/api/embed"
    headers = {"Content-Type": "application/json"}
    key = getattr(settings, "ollama_api_key", None)
    if key:
        headers["Authorization"] = f"Bearer {key}"
    resp = requests.post(
        url,
        json={"model": model, "input": texts},
        headers=headers,
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    embs = data.get("embeddings") or []
    return [list(map(float, e)) for e in embs if e]


def embed_openai_compatible(
    base_url: str,
    model: str,
    texts: list[str],
    api_key: str | None,
    *,
    timeout: float = 120.0,
) -> list[list[float]]:
    url = f"{base_url.rstrip('/')}/v1/embeddings"
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    resp = requests.post(
        url,
        json={"model": model, "input": texts},
        headers=headers,
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()
    rows = data.get("data") or []
    return [list(map(float, r.get("embedding") or [])) for r in rows]


def _chunk_list(lst: list[str], n: int):
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def embed_fastembed(texts: list[str], model_name: str) -> list[list[float]]:
    global _fastembed_model, _fastembed_model_name
    if not texts:
        return []
    try:
        from fastembed import TextEmbedding
    except ImportError:
        logger.warning("FastEmbed não instalado (pip install fastembed).")
        return []
    if _fastembed_model is None or _fastembed_model_name != model_name:
        _fastembed_model = TextEmbedding(model_name=model_name)
        _fastembed_model_name = model_name
    out: list[list[float]] = []
    for batch in _chunk_list(texts, 32):
        for emb in _fastembed_model.embed(batch):
            out.append([float(x) for x in emb])
    return out


def embed_texts_best_effort(texts: list[str]) -> list[list[float]]:
    """
    Orquestra backends conforme EMBEDDING_BACKEND:
    - native: só hash
    - ollama / fastembed / openai_http: forçado
    - auto: Ollama (se URL) → FastEmbed → HTTP local → hash
    """
    if not texts:
        return []
    backend = (getattr(settings, "embedding_backend", None) or "auto").strip().lower()

    if backend == "native":
        return hash_embed_texts(texts)

    if backend == "ollama":
        base = getattr(settings, "ollama_endpoint", None)
        mod = (getattr(settings, "ollama_embed_model", None) or "nomic-embed-text").strip()
        if base:
            try:
                v = embed_ollama(str(base).strip(), mod, texts)
                if v and len(v) == len(texts):
                    return v
            except Exception as exc:
                logger.warning("Ollama embed falhou: %s", exc)
        return hash_embed_texts(texts)

    if backend == "fastembed":
        mn = (
            getattr(settings, "fastembed_model_name", None)
            or "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        ).strip()
        v = embed_fastembed(texts, mn)
        if v and len(v) == len(texts):
            return v
        return hash_embed_texts(texts)

    if backend == "openai_http":
        ep = getattr(settings, "embedding_http_endpoint", None) or getattr(
            settings, "local_llm_endpoint", None
        )
        m = (getattr(settings, "embedding_openai_model", None) or "text-embedding-3-small").strip()
        key = getattr(settings, "openai_api_key", None)
        if ep:
            try:
                v = embed_openai_compatible(str(ep).strip(), m, texts, key)
                if v and len(v) == len(texts):
                    return v
            except Exception as exc:
                logger.warning("Embedding HTTP (/v1/embeddings) falhou: %s", exc)
        return hash_embed_texts(texts)

    # --- auto ---
    base = getattr(settings, "ollama_endpoint", None)
    mod = (getattr(settings, "ollama_embed_model", None) or "nomic-embed-text").strip()
    if base:
        try:
            v = embed_ollama(str(base).strip(), mod, texts)
            if v and len(v) == len(texts):
                return v
        except Exception as exc:
            logger.debug("auto: Ollama embed indisponível: %s", exc)

    mn = (
        getattr(settings, "fastembed_model_name", None)
        or "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    ).strip()
    v = embed_fastembed(texts, mn)
    if v and len(v) == len(texts):
        return v

    ep = getattr(settings, "embedding_http_endpoint", None) or getattr(
        settings, "local_llm_endpoint", None
    )
    if ep:
        m = (getattr(settings, "embedding_openai_model", None) or "text-embedding-3-small").strip()
        key = getattr(settings, "openai_api_key", None)
        try:
            v2 = embed_openai_compatible(str(ep).strip(), m, texts, key)
            if v2 and len(v2) == len(texts):
                return v2
        except Exception as exc:
            logger.debug("auto: embed HTTP ignorado: %s", exc)

    return hash_embed_texts(texts)
