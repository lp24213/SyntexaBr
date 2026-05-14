"""TTS com lazy loading."""
from __future__ import annotations

import base64
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from worker.core.engines import generate_tts

router = APIRouter()


class TTSRequest(BaseModel):
    text: str
    voice: str | None = None
    language: str = "pt-BR"


@router.post("/tts")
def text_to_speech(req: TTSRequest) -> dict[str, Any]:
    try:
        audio = generate_tts(req.text, voice=req.voice)
        b64 = base64.b64encode(audio).decode("ascii")
        return {
            "ok": True,
            "audio_url": f"data:audio/mpeg;base64,{b64}",
            "mime": "audio/mpeg",
            "provider": "edge-tts",
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"TTS failed: {exc}")
