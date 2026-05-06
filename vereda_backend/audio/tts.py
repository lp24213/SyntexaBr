"""Text-to-speech — reutiliza media_engine (Edge TTS ou endpoint local)."""
from __future__ import annotations

from typing import Any, Dict

from vereda_backend.services.media_engine import generate_tts_from_text


def synthesize_text(text: str, voice: str | None = None) -> Dict[str, Any]:
    return generate_tts_from_text(text, voice=voice)
