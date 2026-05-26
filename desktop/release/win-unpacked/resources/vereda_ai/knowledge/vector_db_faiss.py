# -*- coding: utf-8 -*-
"""
Optional FAISS vector backend for RAG. Lightweight, CPU-friendly.
Use when embeddings are available (e.g. via LLMEngine.embed).
Install: pip install faiss-cpu
"""
from typing import Any, Callable, List, Optional

from vereda_ai.knowledge.vector_db import VectorDB


def _default_embed(text: str) -> List[float]:
    """Fallback when no embed_fn: simple hash-based pseudo-vector (low quality)."""
    import hashlib
    h = hashlib.sha256(text.encode()).digest()
    return [float((b - 128) / 128.0) for b in h[:32]]


class FAISSVectorStore(VectorDB):
    """
    Vector store backed by FAISS index. Requires embed_fn for real similarity.
    Optimized for CPU and low memory (no GPU).
    """

    def __init__(
        self,
        embed_fn: Optional[Callable[[str], List[float]]] = None,
        embed_batch_fn: Optional[Callable[[List[str]], List[List[float]]]] = None,
        dimension: int = 384,
    ):
        self._embed_fn = embed_fn or _default_embed
        self._embed_batch_fn = embed_batch_fn
        self._dim = dimension
        self._index = None
        self._id_to_meta: List[dict] = []
        self._namespace_offset: dict = {}
        self._build_index()

    def _build_index(self) -> None:
        try:
            import faiss
            self._index = faiss.IndexFlatL2(self._dim)
        except ImportError:
            self._index = None

    def _embed(self, text: str) -> List[float]:
        if self._embed_batch_fn:
            vectors = self._embed_batch_fn([text])
            return vectors[0] if vectors else _default_embed(text)
        return self._embed_fn(text)

    def add_text(
        self,
        namespace: str,
        doc_id: str,
        text: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        if self._index is None:
            return
        vec = self._embed(text)
        if len(vec) != self._dim:
            vec = vec[:self._dim] + [0.0] * (self._dim - len(vec))
        import numpy as np
        v = np.array([vec], dtype=np.float32)
        self._index.add(v)
        self._id_to_meta.append({
            "id": doc_id,
            "text": text,
            "namespace": namespace,
            "metadata": metadata or {},
        })
        self._namespace_offset.setdefault(namespace, []).append(len(self._id_to_meta) - 1)

    def similarity_search(
        self, namespace: str, query: str, top_k: int = 5
    ) -> List[dict[str, Any]]:
        if self._index is None or not self._id_to_meta:
            return []
        import numpy as np
        q = self._embed(query)
        if len(q) != self._dim:
            q = q[:self._dim] + [0.0] * (self._dim - len(q))
        qv = np.array([q], dtype=np.float32)
        k = min(top_k * 5, self._index.ntotal)  # request extra to filter by namespace
        if k <= 0:
            return []
        scores, indices = self._index.search(qv, k)
        out = []
        for idx, score in zip(indices[0], scores[0]):
            if idx < 0 or idx >= len(self._id_to_meta):
                continue
            meta = self._id_to_meta[idx]
            if meta["namespace"] != namespace:
                continue
            # L2 distance -> lower is better; convert to simple score in [0,1]
            sim = 1.0 / (1.0 + float(score))
            out.append({
                "text": meta["text"],
                "source": meta.get("metadata", {}).get("source", "indexed"),
                "score": sim,
                **meta.get("metadata", {}),
            })
            if len(out) >= top_k:
                break
        return out
