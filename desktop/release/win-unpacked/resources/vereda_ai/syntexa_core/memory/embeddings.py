"""
SYNTEXA EMBEDDINGS
==================
Motor de embeddings local para RAG, memória e retrieval semântico.
Sem dependência de APIs externas.
"""
from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


class SyntexaEmbeddings:
    """
    Gera embeddings de texto localmente.
    Backends (por ordem de preferência):
    1. sentence-transformers (ONNX/cpu)
    2. fastembed (ONNX puro)
    3. determinístico hash (fallback de último recurso, apenas para tests)
    """

    def __init__(self, model_name: Optional[str] = None, dim: int = 384, device: Optional[str] = None):
        self.model_name = model_name or "all-MiniLM-L6-v2"
        self.dim = dim
        self.device = device or ("cuda" if self._cuda_available() else "cpu")
        self._backend: Optional[str] = None
        self._model: Optional[object] = None

    def _cuda_available(self) -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except Exception:
            return False

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return

        # 1) sentence-transformers
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("[SyntexaEmbeddings] Carregando sentence-transformers: %s", self.model_name)
            self._model = SentenceTransformer(self.model_name, device=self.device)
            self.dim = self._model.get_sentence_embedding_dimension()  # type: ignore[attr-defined]
            self._backend = "sentence-transformers"
            return
        except Exception as exc:
            logger.debug("sentence-transformers não disponível: %s", exc)

        # 2) fastembed
        try:
            from fastembed import TextEmbedding
            logger.info("[SyntexaEmbeddings] Carregando fastembed: %s", self.model_name)
            self._model = TextEmbedding(model_name=self.model_name)
            self._backend = "fastembed"
            return
        except Exception as exc:
            logger.debug("fastembed não disponível: %s", exc)

        logger.warning("[SyntexaEmbeddings] Usando fallback hash determinístico (NÃO para produção)")
        self._backend = "hash"

    def embed(self, texts: list[str]) -> list[list[float]]:
        self._ensure_loaded()
        if not texts:
            return []

        if self._backend == "sentence-transformers":
            vecs = self._model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)  # type: ignore[attr-defined]
            return vecs.tolist()

        if self._backend == "fastembed":
            vecs = list(self._model.embed(texts))  # type: ignore[attr-defined]
            return [v.tolist() for v in vecs]

        # fallback hash
        return self._hash_embed(texts)

    def _hash_embed(self, texts: list[str]) -> list[list[float]]:
        vecs = []
        for t in texts:
            h = hashlib.sha256(t.encode("utf-8")).digest()
            arr = np.frombuffer(h, dtype=np.uint8).astype(np.float32)[: self.dim]
            if len(arr) < self.dim:
                arr = np.pad(arr, (0, self.dim - len(arr)), mode="constant")
            norm = np.linalg.norm(arr)
            if norm > 0:
                arr = arr / norm
            vecs.append(arr.tolist())
        return vecs

    def embed_query(self, text: str) -> list[float]:
        return self.embed([text])[0]
