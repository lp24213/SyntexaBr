"""Embeddings com lazy loading."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from worker.core.engines import embed_texts

router = APIRouter()


class EmbeddingsRequest(BaseModel):
    texts: list[str]
    model: str | None = "default"


@router.post("/embeddings")
def embeddings(req: EmbeddingsRequest) -> dict[str, Any]:
    try:
        vectors = embed_texts(req.texts)
        return {
            "data": [
                {"index": i, "embedding": vec, "object": "embedding"}
                for i, vec in enumerate(vectors)
            ],
            "model": req.model or "default",
            "usage": {"prompt_tokens": sum(len(t.split()) for t in req.texts), "total_tokens": sum(len(t.split()) for t in req.texts)},
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {exc}")
