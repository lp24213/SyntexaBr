"""Proxy para embeddings — encaminha para AI Worker."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from gateway.core.ai_proxy import proxy_embeddings_sync

router = APIRouter()


class EmbeddingsRequest(BaseModel):
    texts: list[str]
    model: str | None = "default"


@router.post("/embeddings")
def embeddings(req: EmbeddingsRequest) -> dict[str, Any]:
    try:
        return proxy_embeddings_sync(texts=req.texts, model=req.model)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"IA Worker indisponível: {exc}")
