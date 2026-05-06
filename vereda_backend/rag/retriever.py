# -*- coding: utf-8 -*-
"""Recuperação de trechos indexados (RAG) sobre o vector store existente."""
from __future__ import annotations

from typing import Any, List


def retrieve_rag_chunks(
    rag_db: Any,
    *,
    namespace: str,
    query: str,
    top_k: int = 5,
) -> List[dict]:
    if not hasattr(rag_db, "similarity_search"):
        return []
    return rag_db.similarity_search(namespace=namespace, query=query, top_k=top_k)
