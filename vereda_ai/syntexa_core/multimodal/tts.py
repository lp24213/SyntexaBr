"""
SYNTEXA TTS (Text-to-Speech)
============================
Síntese de voz local.
Interface soberana; usa Coqui TTS / Piper quando disponíveis.
"""
from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SyntexaTTS:
    """
    Motor TTS soberano da Syntexa.
    Backends: Coqui TTS (preferido) ou Piper (fallback).
    """

    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None):
        self.model_name = model_name
        self.device = device or ("cuda" if self._cuda_available() else "cpu")
        self._model: Optional[object] = None
        self._backend: Optional[str] = None

    def _cuda_available(self) -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except Exception:
            return False

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        # Tenta Coqui TTS
        try:
            from TTS.api import TTS
            logger.info("[SyntexaTTS] Carregando Coqui TTS...")
            model = self.model_name or "tts_models/multilingual/multi-dataset/xtts_v2"
            self._model = TTS(model).to(self.device)
            self._backend = "coqui"
            return
        except Exception as exc:
            logger.debug("Coqui TTS não disponível: %s", exc)

        # Fallback Piper
        try:
            from piper import PiperVoice
            logger.info("[SyntexaTTS] Carregando Piper TTS...")
            self._model = PiperVoice.load(self.model_name or "pt_BR-faber-medium")
            self._backend = "piper"
            return
        except Exception as exc:
            logger.debug("Piper não disponível: %s", exc)

        raise RuntimeError(
            "Nenhum backend TTS disponível. Instale: pip install TTS  (ou piper-tts)"
        )

    def synthesize(self, text: str, output_path: Optional[str] = None, speaker_wav: Optional[str] = None) -> str:
        """
        Sintetiza texto em áudio. Retorna caminho do arquivo WAV gerado.
        """
        self._ensure_loaded()
        if output_path is None:
            fd, output_path = tempfile.mkstemp(suffix=".wav")
            Path(fd).close()

        if self._backend == "coqui":
            kwargs: dict = {"file_path": output_path, "text": text}
            if speaker_wav:
                kwargs["speaker_wav"] = speaker_wav
                kwargs["language"] = "pt"
            self._model.tts_to_file(**kwargs)  # type: ignore[attr-defined]
        elif self._backend == "piper":
            import wave
            with wave.open(output_path, "wb") as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(22050)
                for audio_bytes in self._model.synthesize_stream_raw(text):  # type: ignore[attr-defined]
                    wav_file.writeframes(audio_bytes)
        else:
            raise RuntimeError(f"Backend TTS desconhecido: {self._backend}")

        return str(output_path)

    def synthesize_bytes(self, text: str, speaker_wav: Optional[str] = None) -> bytes:
        """Sintetiza e retorna bytes WAV."""
        path = self.synthesize(text, speaker_wav=speaker_wav)
        data = Path(path).read_bytes()
        Path(path).unlink(missing_ok=True)
        return data
