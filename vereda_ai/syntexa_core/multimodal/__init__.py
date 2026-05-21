"""
SYNTEXA MULTIMODAL STACK
========================
STT, TTS, OCR, Vision — interfaces soberanas com backends locais.
"""
from __future__ import annotations

from .stt import SyntexaSTT
from .tts import SyntexaTTS
from .ocr import SyntexaOCR
from .vision import SyntexaVisionEncoder

__all__ = ["SyntexaSTT", "SyntexaTTS", "SyntexaOCR", "SyntexaVisionEncoder"]
