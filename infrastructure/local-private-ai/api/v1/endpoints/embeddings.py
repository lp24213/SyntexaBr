"""Embeddings via Ollama."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from local_private_ai.core.ollama_client import ollama_embeddings

router = APIRouter()


class EmbeddingsRequest(BaseModel):
    texts: list[str]
    model: str | None = None


@router.post("/embeddings")
def embeddings(req: EmbeddingsRequest) -> dict[str, Any]:
    try:
        result = ollama_embeddings(req.texts, model=req.model)
        vectors = result.get("embeddings", [])
        return {
            "data": [
                {"index": i, "embedding": vec, "object": "embedding"}
                for i, vec in enumerate(vectors)
            ],
            "model": req.model or "default",
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Ollama embedding error: {exc}")
