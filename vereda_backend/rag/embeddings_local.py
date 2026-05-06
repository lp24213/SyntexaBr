# -*- coding: utf-8 -*-
"""Embeddings via motor LLM já registado (syntexa_native ou gateway HTTP configurado)."""
from __future__ import annotations

from typing import List


def embed_texts_local(texts: List[str]) -> List[List[float]]:
    from vereda_backend.ai_runtime import llm_engine

    if not texts:
        return []
    # Vetores sempre pelo núcleo Syntexa (RAG/treino estáveis), mesmo com DEFAULT_LLM=ollama.
    return llm_engine.embed(texts, provider="syntexa_native")
