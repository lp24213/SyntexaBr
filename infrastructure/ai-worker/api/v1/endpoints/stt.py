"""STT com lazy loading de Whisper."""
from __future__ import annotations

import tempfile
from typing import Any

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from worker.core.engines import transcribe_audio

router = APIRouter()


@router.post("/stt")
def speech_to_text(
    audio: UploadFile = File(...),
    language: str = Form("pt"),
) -> dict[str, Any]:
    try:
        suffix = ".mp3"
        content_type = audio.content_type or ""
        if "wav" in content_type:
            suffix = ".wav"
        elif "ogg" in content_type:
            suffix = ".ogg"

        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(audio.file.read())
            tmp_path = tmp.name

        result = transcribe_audio(tmp_path, language=language)
        return {"ok": True, **result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"STT failed: {exc}")
