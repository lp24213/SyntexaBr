"""
SYNTEXA VECTOR STORE & RAG
==========================
Vector database local e pipeline RAG soberano.
Sem dependência de Pinecone, Weaviate, etc.
Backends: FAISS (preferido), Annoy, ou brute-force numpy.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from vereda_ai.syntexa_core.memory.embeddings import SyntexaEmbeddings

logger = logging.getLogger(__name__)


@dataclass
class Document:
    id: str
    text: str
    embedding: Optional[list[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class SyntexaVectorStore:
    """
    Vector store local com busca por similaridade de cosseno.
    """

    def __init__(self, dim: int = 384, backend: str = "auto"):
        self.dim = dim
        self.docs: list[Document] = []
        self._vectors: Optional[np.ndarray] = None
        self._backend_name = backend
        self._index: Optional[Any] = None

    def _ensure_index(self) -> None:
        if self._index is not None:
            return
        if not self.docs:
            return

        vecs = np.array([d.embedding for d in self.docs if d.embedding], dtype=np.float32)
        if vecs.shape[0] == 0:
            return

        if self._backend_name == "auto":
            # Tenta FAISS -> Annoy -> numpy
            try:
                import faiss
                self._index = faiss.IndexFlatIP(self.dim)
                self._index.add(vecs)  # type: ignore[attr-defined]
                self._backend_name = "faiss"
                logger.info("[VectorStore] Usando FAISS (docs=%d)", len(self.docs))
                return
            except Exception as exc:
                logger.debug("FAISS não disponível: %s", exc)

            try:
                from annoy import AnnoyIndex
                self._index = AnnoyIndex(self.dim, "angular")
                for i, v in enumerate(vecs):
                    self._index.add_item(i, v)
                self._index.build(10)
                self._backend_name = "annoy"
                logger.info("[VectorStore] Usando Annoy (docs=%d)", len(self.docs))
                return
            except Exception as exc:
                logger.debug("Annoy não disponível: %s", exc)

        self._vectors = vecs
        self._backend_name = "numpy"
        logger.info("[VectorStore] Usando brute-force numpy (docs=%d)", len(self.docs))

    def add_documents(self, documents: list[Document], embeddings: Optional[SyntexaEmbeddings] = None) -> None:
        if embeddings:
            texts = [d.text for d in documents]
            vecs = embeddings.embed(texts)
            for d, v in zip(documents, vecs):
                d.embedding = v
        self.docs.extend(documents)
        # Invalida índice
        self._index = None
        self._vectors = None
        self._backend_name = "auto" if self._backend_name == "auto" else self._backend_name

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 5,
    ) -> list[tuple[Document, float]]:
        self._ensure_index()
        q = np.array(query_embedding, dtype=np.float32).reshape(1, -1)

        if self._backend_name == "faiss" and self._index is not None:
            scores, indices = self._index.search(q, top_k)  # type: ignore[attr-defined]
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx >= 0 and idx < len(self.docs):
                    results.append((self.docs[idx], float(score)))
            return results

        if self._backend_name == "annoy" and self._index is not None:
            indices, distances = self._index.get_nns_by_vector(q[0], top_k, include_distances=True)  # type: ignore[attr-defined]
            results = []
            for idx, dist in zip(indices, distances):
                # Annoy retorna distância angular; convertemos para similaridade
                sim = 1.0 - (dist ** 2) / 2.0
                results.append((self.docs[idx], float(sim)))
            return results

        # Numpy brute-force
        if self._vectors is not None:
            sims = (self._vectors @ q.T).flatten()
            top_indices = np.argsort(-sims)[:top_k]
            return [(self.docs[i], float(sims[i])) for i in top_indices]

        return []

    def save(self, path: str | Path) -> None:
        out = Path(path)
        out.mkdir(parents=True, exist_ok=True)
        data = []
        for d in self.docs:
            data.append({
                "id": d.id,
                "text": d.text,
                "embedding": d.embedding,
                "metadata": d.metadata,
            })
        (out / "docs.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "SyntexaVectorStore":
        out = Path(path)
        data = json.loads((out / "docs.json").read_text(encoding="utf-8"))
        store = cls()
        for item in data:
            store.docs.append(Document(
                id=item["id"],
                text=item["text"],
                embedding=item.get("embedding"),
                metadata=item.get("metadata", {}),
            ))
        return store


class SyntexaRAG:
    """
    Pipeline RAG soberano: retrieve + generate com contexto injetado.
    """

    def __init__(
        self,
        vector_store: SyntexaVectorStore,
        embeddings: SyntexaEmbeddings,
        inference_engine: Optional[Any] = None,
        top_k: int = 5,
        context_max_tokens: int = 1500,
    ):
        self.vector_store = vector_store
        self.embeddings = embeddings
        self.inference_engine = inference_engine
        self.top_k = top_k
        self.context_max_tokens = context_max_tokens

    def retrieve(self, query: str) -> list[tuple[Document, float]]:
        q_emb = self.embeddings.embed_query(query)
        return self.vector_store.search(q_emb, top_k=self.top_k)

    def build_context(self, query: str) -> str:
        results = self.retrieve(query)
        if not results:
            return ""
        chunks: list[str] = []
        total_len = 0
        for doc, score in results:
            chunk = f"[score={score:.3f}] {doc.text}"
            total_len += len(chunk)
            if total_len > self.context_max_tokens * 4:  # heurística chars/tokens
                break
            chunks.append(chunk)
        return "\n\n".join(chunks)

    def query(self, question: str, system_prompt: Optional[str] = None) -> str:
        if self.inference_engine is None:
            raise RuntimeError("InferenceEngine não configurado no RAG.")
        context = self.build_context(question)
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        if context:
            messages.append({"role": "system", "content": f"Contexto relevante:\n{context}"})
        messages.append({"role": "user", "content": question})
        return self.inference_engine.chat(messages)
