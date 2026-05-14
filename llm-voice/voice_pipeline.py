"""
VEREDA / SYNTEXA — Voice Pipeline
==================================
Pipeline completa de voz com:
- VAD (Voice Activity Detection)
- STT → LLM → TTS
- Emotion detection
- Realtime streaming
"""

import logging
from typing import AsyncIterator, Dict, Optional, Any
from dataclasses import dataclass

from .stt_engine import STTEngine
from .tts_engine import TTSEngine

log = logging.getLogger(__name__)


@dataclass
class VoicePipelineConfig:
    stt_model: str = "base"
    tts_voice: str = "pt-BR-FranciscaNeural"
    language: str = "pt-BR"
    vad_threshold: float = -40.0
    max_recording_sec: float = 60.0
    stream_chunks: bool = True


class VoicePipeline:
    """
    Pipeline de voz: STT → processamento → TTS.
    """

    def __init__(self, config: Optional[VoicePipelineConfig] = None):
        self.config = config or VoicePipelineConfig()
        self.stt = STTEngine(model_size=self.config.stt_model)
        self.tts = TTSEngine(default_voice=self.config.tts_voice)

    # ── FULL PIPELINE ────────────────────────────────────────
    def process(self, audio_data: bytes, llm_fn=None) -> Dict[str, Any]:
        """
        Pipeline completo: áudio → texto → resposta → áudio.
        """
        # 1. STT
        stt_result = self.stt.transcribe(audio_data)
        if not stt_result.text:
            return {
                "success": False,
                "error": "Não foi possível transcrever o áudio",
                "stt": stt_result.__dict__,
            }

        # 2. LLM Processing
        if llm_fn:
            llm_response = llm_fn(stt_result.text)
        else:
            llm_response = f"Você disse: {stt_result.text}"

        # 3. TTS
        tts_result = self.tts.synthesize(
            llm_response,
            voice=self.config.tts_voice,
            language=self.config.language,
        )

        return {
            "success": True,
            "transcript": stt_result.text,
            "response_text": llm_response,
            "stt": {
                "language": stt_result.language,
                "confidence": stt_result.confidence,
                "duration": stt_result.duration_sec,
            },
            "tts": {
                "voice": tts_result.voice,
                "duration": tts_result.duration_sec,
                "format": tts_result.format,
                "audio_base64": tts_result.audio_base64,
            },
        }

    # ── STREAMING PIPELINE ─────────────────────────────────
    async def process_stream(
        self,
        audio_stream: AsyncIterator[bytes],
        llm_fn=None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Pipeline em tempo real.
        """
        buffer = bytearray()
        is_recording = False

        async for chunk in audio_stream:
            buffer.extend(chunk)

            # VAD check every chunk
            if len(buffer) > 16000:  # ~1 second at 16kHz
                has_voice = self.stt.detect_voice_activity(bytes(buffer), self.config.vad_threshold)

                if has_voice and not is_recording:
                    is_recording = True
                    yield {"event": "speech_started"}

                elif not has_voice and is_recording:
                    is_recording = False
                    # Process accumulated audio
                    result = self.process(bytes(buffer), llm_fn)
                    yield {"event": "speech_ended", "result": result}
                    buffer.clear()

        # Process remaining audio
        if buffer:
            result = self.process(bytes(buffer), llm_fn)
            yield {"event": "final", "result": result}

    # ── CONVERSATION PIPELINE ────────────────────────────────
    def process_conversation_turn(
        self,
        audio_data: bytes,
        conversation_history: list,
        llm_fn=None,
    ) -> Dict[str, Any]:
        """
        Processa um turno de conversação por voz.
        """
        # Transcreve
        stt_result = self.stt.transcribe(audio_data)

        # Adiciona ao histórico
        conversation_history.append({
            "role": "user",
            "content": stt_result.text,
            "modality": "voice",
        })

        # Gera resposta com contexto
        if llm_fn:
            llm_response = llm_fn(stt_result.text, context=conversation_history)
        else:
            llm_response = f"Resposta para: {stt_result.text}"

        # Adiciona resposta ao histórico
        conversation_history.append({
            "role": "assistant",
            "content": llm_response,
            "modality": "voice",
        })

        # Síntese
        tts_result = self.tts.synthesize(llm_response)

        return {
            "transcript": stt_result.text,
            "response": llm_response,
            "audio_base64": tts_result.audio_base64,
            "conversation_length": len(conversation_history),
        }
