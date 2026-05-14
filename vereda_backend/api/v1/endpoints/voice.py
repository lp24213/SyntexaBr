"""
VEREDA / SYNTEXA — Voice API v1
================================
STT + TTS via AI Router (AWS GPU → Local fallback)
"""
from typing import Any, Dict

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from starlette.responses import StreamingResponse

from vereda_backend.core.security import get_current_user_optional
from vereda_backend.db import models
from vereda_backend.services.ai_router import get_ai_router_service

router = APIRouter(prefix="/voice")


@router.post("/stt")
async def voice_stt(
    file: UploadFile = File(...),
    current_user: models.User | None = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    """Speech-to-Text: upload de áudio → texto."""
    data = await file.read()
    if len(data) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Áudio muito grande (máx. 50 MB).")

    import base64
    audio_b64 = base64.b64encode(data).decode("utf-8")
    service = get_ai_router_service()
    return await service.voice_stt(audio_b64, filename=file.filename or "audio.wav")


@router.post("/tts")
async def voice_tts(
    text: str = Form(...),
    voice: str | None = Form(None),
    current_user: models.User | None = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    """Text-to-Speech: texto → áudio."""
    if not text.strip():
        raise HTTPException(status_code=400, detail="Texto vazio.")
    service = get_ai_router_service()
    return await service.voice_tts(text, voice=voice)


@router.get("/health")
async def voice_health() -> Dict[str, Any]:
    """Saúde dos backends de voz."""
    service = get_ai_router_service()
    return await service.health()
