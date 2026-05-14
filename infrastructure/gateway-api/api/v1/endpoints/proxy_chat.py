"""Proxy para chat completions — encaminha para AI Worker ou Local AI."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from gateway.core.ai_proxy import proxy_chat_completion_sync

router = APIRouter()


class ChatRequest(BaseModel):
    messages: list[dict[str, str]]
    model: str | None = "default"
    stream: bool = False
    temperature: float = 0.7
    max_tokens: int = 2048


@router.post("/chat/completions")
def chat_completions(req: ChatRequest) -> dict[str, Any]:
    try:
        return proxy_chat_completion_sync(
            messages=req.messages,
            model=req.model,
            stream=req.stream,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"IA Worker indisponível: {exc}")
