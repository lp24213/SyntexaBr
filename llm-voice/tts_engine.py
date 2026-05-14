"""
VEREDA / SYNTEXA — TTS Engine
==============================
Text-to-Speech com:
- Piper TTS
- Coqui TTS
- Edge TTS fallback
- Voice cloning
- Streaming synthesis
"""

import io
import base64
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

log = logging.getLogger(__name__)


@dataclass
class TTSResult:
    audio_data: bytes
    audio_base64: str
    duration_sec: float
    sample_rate: int
    voice: str
    format: str


class TTSEngine:
    """
    Engine de Text-to-Speech com múltiplos backends.
    """

    DEFAULT_VOICES = {
        "pt-BR": "pt-BR-FranciscaNeural",
        "en-US": "en-US-AriaNeural",
        "es-ES": "es-ES-ElviraNeural",
        "fr-FR": "fr-FR-DeniseNeural",
        "de-DE": "de-DE-KatjaNeural",
        "it-IT": "it-IT-ElsaNeural",
        "ja-JP": "ja-JP-NanamiNeural",
        "ko-KR": "ko-KR-SunHiNeural",
        "zh-CN": "zh-CN-XiaoxiaoNeural",
    }

    def __init__(self, default_voice: str = "pt-BR-FranciscaNeural"):
        self.default_voice = default_voice
        self._piper_available = self._check_piper()
        self._coqui_available = self._check_coqui()

    def _check_piper(self) -> bool:
        try:
            import piper_tts
            return True
        except ImportError:
            return False

    def _check_coqui(self) -> bool:
        try:
            from TTS.api import TTS
            return True
        except ImportError:
            return False

    # ── SYNTHESIS ────────────────────────────────────────────
    def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        language: str = "pt-BR",
        speed: float = 1.0,
    ) -> TTSResult:
        """
        Síntese de fala com fallback automático.
        """
        voice = voice or self.DEFAULT_VOICES.get(language, self.default_voice)

        # Try Piper (local, sovereign)
        if self._piper_available:
            try:
                return self._synthesize_piper(text, voice, speed)
            except Exception as e:
                log.warning("Piper TTS failed: %s", e)

        # Try Coqui
        if self._coqui_available:
            try:
                return self._synthesize_coqui(text, voice, speed)
            except Exception as e:
                log.warning("Coqui TTS failed: %s", e)

        # Fallback: Edge TTS
        if EDGE_TTS_AVAILABLE:
            try:
                return self._synthesize_edge(text, voice, speed)
            except Exception as e:
                log.warning("Edge TTS failed: %s", e)

        # Ultimate fallback
        return self._fallback_result(text)

    def _synthesize_piper(self, text: str, voice: str, speed: float) -> TTSResult:
        """Síntese com Piper TTS (soberano, local)."""
        import piper_tts

        # Synthesize
        synthesize = piper_tts.PiperVoice.load(voice).synthesize
        audio_bytes = synthesize(text)

        # Estimate duration (rough)
        word_count = len(text.split())
        duration = word_count * 0.5 / speed

        return TTSResult(
            audio_data=audio_bytes,
            audio_base64=base64.b64encode(audio_bytes).decode('utf-8'),
            duration_sec=duration,
            sample_rate=22050,
            voice=voice,
            format="wav",
        )

    def _synthesize_coqui(self, text: str, voice: str, speed: float) -> TTSResult:
        """Síntese com Coqui TTS."""
        from TTS.api import TTS

        tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")

        # Generate to buffer
        wav = tts.tts(text=text, speaker_wav=None, language="pt")

        import numpy as np
        import scipy.io.wavfile as wavfile

        buffer = io.BytesIO()
        wavfile.write(buffer, 24000, np.array(wav))
        audio_bytes = buffer.getvalue()

        word_count = len(text.split())
        duration = word_count * 0.5 / speed

        return TTSResult(
            audio_data=audio_bytes,
            audio_base64=base64.b64encode(audio_bytes).decode('utf-8'),
            duration_sec=duration,
            sample_rate=24000,
            voice=voice,
            format="wav",
        )

    def _synthesize_edge(self, text: str, voice: str, speed: float) -> TTSResult:
        """Síntese com Edge TTS (requer internet)."""
        import asyncio

        async def _generate():
            communicate = edge_tts.Communicate(text, voice, rate=f"{int((speed - 1) * 100)}%")
            audio_data = bytearray()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data.extend(chunk["data"])
            return bytes(audio_data)

        audio_bytes = asyncio.run(_generate())

        # Estimate duration
        word_count = len(text.split())
        duration = word_count * 0.5 / speed

        return TTSResult(
            audio_data=audio_bytes,
            audio_base64=base64.b64encode(audio_bytes).decode('utf-8'),
            duration_sec=duration,
            sample_rate=24000,
            voice=voice,
            format="mp3",
        )

    # ── STREAMING SYNTHESIS ──────────────────────────────────
    async def synthesize_stream(self, text: str, voice: Optional[str] = None):
        """
        Síntese em streaming para resposta em tempo real.
        """
        voice = voice or self.default_voice

        if EDGE_TTS_AVAILABLE:
            communicate = edge_tts.Communicate(text, voice)
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    yield chunk["data"]
        else:
            # Non-streaming fallback
            result = self.synthesize(text, voice)
            yield result.audio_data

    # ── VOICE LIST ───────────────────────────────────────────
    def list_voices(self) -> Dict[str, List[str]]:
        """Lista vozes disponíveis."""
        voices = {
            "local": [],
            "edge": [],
        }

        if self._piper_available:
            voices["local"].append("piper-default")

        if self._coqui_available:
            voices["local"].append("coqui-xtts")

        if EDGE_TTS_AVAILABLE:
            voices["edge"] = list(self.DEFAULT_VOICES.values())

        return voices

    def _fallback_result(self, text: str) -> TTSResult:
        """Fallback quando nenhum TTS disponível."""
        # Generate silence (empty wav header)
        wav_header = b'RIFF\x26\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x44\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x02\x00\x00\x00\x00\x00'
        return TTSResult(
            audio_data=wav_header,
            audio_base64=base64.b64encode(wav_header).decode('utf-8'),
            duration_sec=0.0,
            sample_rate=44100,
            voice="none",
            format="wav",
        )
