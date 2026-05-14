"""Proxy para mídia (OCR, TTS, STT) — encaminha para AI Worker ou Local AI."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from gateway.core.ai_proxy import proxy_to_ai_worker_sync, proxy_to_local_ai_sync

router = APIRouter()


class TTSRequest(BaseModel):
    text: str
    voice: str | None = None
    language: str = "pt-BR"


class OCRRequest(BaseModel):
    image_base64: str
    language: str = "por"


@router.post("/tts")
def text_to_speech(req: TTSRequest) -> dict[str, Any]:
    try:
        return proxy_to_ai_worker_sync("/v1/tts", {"text": req.text, "voice": req.voice, "language": req.language}, timeout_sec=60.0)
    except Exception:
        try:
            return proxy_to_local_ai_sync("/v1/tts", {"text": req.text, "voice": req.voice, "language": req.language}, timeout_sec=60.0)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"TTS indisponível: {exc}")


@router.post("/stt")
def speech_to_text(audio: UploadFile = File(...), language: str = Form("pt-BR")) -> dict[str, Any]:
    try:
        return proxy_to_ai_worker_sync("/v1/stt", {"language": language}, timeout_sec=120.0)
    except Exception:
        try:
            return proxy_to_local_ai_sync("/v1/stt", {"language": language}, timeout_sec=120.0)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"STT indisponível: {exc}")


@router.post("/ocr")
def optical_character_recognition(req: OCRRequest) -> dict[str, Any]:
    try:
        return proxy_to_ai_worker_sync("/v1/ocr", {"image_base64": req.image_base64, "language": req.language}, timeout_sec=60.0)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OCR indisponível: {exc}")
