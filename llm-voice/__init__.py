"""
VEREDA / SYNTEXA — Voice Engine
================================
Engine de voz soberana com:
- STT (Speech-to-Text)
- TTS (Text-to-Speech)
- Voice activity detection
- Emotion detection
- Realtime streaming
"""

from .stt_engine import STTEngine
from .tts_engine import TTSEngine
from .voice_pipeline import VoicePipeline

__all__ = [
    "STTEngine",
    "TTSEngine",
    "VoicePipeline",
]
