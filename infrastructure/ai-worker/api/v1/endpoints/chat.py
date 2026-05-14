"""Chat completions com lazy loading de LLM."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from worker.core.engines import generate_text

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
        text = generate_text(
            req.messages,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
        )
        return {
            "choices": [
                {
                    "message": {"role": "assistant", "content": text},
                    "finish_reason": "stop",
                    "index": 0,
                }
            ],
            "model": req.model or "default",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Generation failed: {exc}")
