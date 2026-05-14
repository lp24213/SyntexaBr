"""Chat completions via Ollama."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from local_private_ai.core.ollama_client import ollama_chat

router = APIRouter()


class ChatRequest(BaseModel):
    messages: list[dict[str, str]]
    model: str | None = None
    stream: bool = False
    temperature: float = 0.7
    max_tokens: int = 2048


@router.post("/chat/completions")
def chat_completions(req: ChatRequest) -> dict[str, Any]:
    try:
        result = ollama_chat(req.messages, model=req.model, stream=req.stream)
        return {
            "choices": [
                {
                    "message": {"role": "assistant", "content": result.get("message", {}).get("content", "")},
                    "finish_reason": "stop",
                    "index": 0,
                }
            ],
            "model": req.model or "default",
        }
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Ollama error: {exc}")
