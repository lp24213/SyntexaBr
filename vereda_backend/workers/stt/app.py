from __future__ import annotations

import os
import tempfile
import time
from typing import Any

from fastapi import FastAPI, File, Form, UploadFile
from faster_whisper import WhisperModel

app = FastAPI(title="syntexa-stt")

_model_name = os.getenv("WHISPER_MODEL", "large-v3")
_compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "float16")
_device = os.getenv("WHISPER_DEVICE", "cuda")
_default_lang = os.getenv("STT_LANGUAGE", "pt")

model = WhisperModel(_model_name, device=_device, compute_type=_compute_type)


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "service": "syntexa-stt",
        "model": _model_name,
        "device": _device,
    }


@app.post("/transcribe")
async def transcribe(
    audio: UploadFile = File(...),
    language: str = Form(default=_default_lang),
) -> dict[str, Any]:
    t0 = time.perf_counter()
    suffix = ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await audio.read())
        path = tmp.name

    segments, info = model.transcribe(path, language=language, vad_filter=True)
    items = []
    text_parts = []
    for seg in segments:
        items.append(
            {"start": float(seg.start), "end": float(seg.end), "text": seg.text.strip()}
        )
        text_parts.append(seg.text.strip())

    return {
        "ok": True,
        "text": " ".join(p for p in text_parts if p).strip(),
        "segments": items,
        "language": getattr(info, "language", language),
        "duration_sec": round(time.perf_counter() - t0, 3),
    }
