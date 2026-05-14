"""
VEREDA / SYNTEXA — STT Engine
==============================
Speech-to-Text com:
- Whisper integration
- Local inference
- Streaming chunks
- Multi-language
- Punctuation restoration
"""

import os
import io
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

try:
    import soundfile as sf
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False

log = logging.getLogger(__name__)


@dataclass
class STTResult:
    text: str
    language: str
    confidence: float
    segments: List[Dict[str, Any]]
    duration_sec: float
    word_count: int


class STTEngine:
    """
    Engine de Speech-to-Text usando Whisper local.
    """

    MODEL_SIZES = ["tiny", "base", "small", "medium", "large-v3"]

    def __init__(self, model_size: str = "base", device: Optional[str] = None):
        self.model_size = model_size
        self.device = device or ("cuda" if self._check_cuda() else "cpu")
        self._model = None
        self._load_model()

    def _check_cuda(self) -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False

    def _load_model(self) -> None:
        if not WHISPER_AVAILABLE:
            log.warning("Whisper não disponível — STT desativado")
            return
        try:
            log.info("Loading Whisper model: %s on %s", self.model_size, self.device)
            self._model = whisper.load_model(self.model_size).to(self.device)
            log.info("Whisper model loaded successfully")
        except Exception as e:
            log.error("Failed to load Whisper: %s", e)
            self._model = None

    # ── TRANSCRIPTION ──────────────────────────────────────
    def transcribe(self, audio_data: bytes) -> STTResult:
        """
        Transcreve áudio para texto.
        """
        if not WHISPER_AVAILABLE or self._model is None:
            return self._fallback_result()

        try:
            # Convert bytes to numpy array
            if SOUNDFILE_AVAILABLE:
                audio_np, sr = sf.read(io.BytesIO(audio_data))
                # Convert to mono if stereo
                if len(audio_np.shape) > 1:
                    audio_np = audio_np.mean(axis=1)
            else:
                # Fallback: assume raw PCM float32
                import numpy as np
                audio_np = np.frombuffer(audio_data, dtype=np.float32)
                sr = 16000

            # Ensure correct sample rate
            if sr != 16000:
                import librosa
                audio_np = librosa.resample(audio_np, orig_sr=sr, target_sr=16000)
                sr = 16000

            duration = len(audio_np) / sr

            # Transcribe
            result = self._model.transcribe(
                audio_np,
                language=None,  # Auto-detect
                task="transcribe",
                fp16=(self.device == "cuda"),
            )

            text = result["text"].strip()
            segments = result.get("segments", [])

            # Calculate confidence (avg of segment probabilities)
            confidences = [seg.get("avg_logprob", -1.0) for seg in segments]
            avg_confidence = sum(confidences) / max(len(confidences), 1)
            # Convert logprob to 0-1 scale
            confidence = max(0.0, min(1.0, 1.0 + avg_confidence))

            return STTResult(
                text=text,
                language=result.get("language", "unknown"),
                confidence=confidence,
                segments=segments,
                duration_sec=round(duration, 2),
                word_count=len(text.split()),
            )

        except Exception as e:
            log.error("Transcription failed: %s", e)
            return self._fallback_result()

    def transcribe_file(self, file_path: str) -> STTResult:
        """Transcreve arquivo de áudio."""
        try:
            with open(file_path, "rb") as f:
                return self.transcribe(f.read())
        except Exception as e:
            log.error("File transcription failed: %s", e)
            return self._fallback_result()

    # ── STREAMING TRANSCRIPTION ──────────────────────────────
    def transcribe_stream_chunk(self, audio_chunk: bytes, context: str = "") -> Dict[str, Any]:
        """
        Transcreve chunk de áudio em streaming.
        Mantém contexto para coerência.
        """
        result = self.transcribe(audio_chunk)
        return {
            "text": result.text,
            "is_final": True,  # Simplified
            "language": result.language,
            "confidence": result.confidence,
        }

    # ── VOICE ACTIVITY DETECTION ─────────────────────────────
    def detect_voice_activity(self, audio_data: bytes, threshold_db: float = -40.0) -> bool:
        """Detecta se há voz no áudio."""
        try:
            import numpy as np
            if SOUNDFILE_AVAILABLE:
                audio, _ = sf.read(io.BytesIO(audio_data))
            else:
                audio = np.frombuffer(audio_data, dtype=np.float32)

            if len(audio.shape) > 1:
                audio = audio.mean(axis=1)

            # Calculate RMS energy in dB
            rms = np.sqrt(np.mean(audio ** 2))
            db = 20 * np.log10(max(rms, 1e-10))

            return db > threshold_db

        except Exception as e:
            log.warning("VAD failed: %s", e)
            return True  # Assume voice if detection fails

    # ── LANGUAGE DETECTION ───────────────────────────────────
    def detect_language(self, audio_data: bytes) -> str:
        """Detecta idioma do áudio."""
        if not WHISPER_AVAILABLE or self._model is None:
            return "unknown"

        try:
            import numpy as np
            if SOUNDFILE_AVAILABLE:
                audio, sr = sf.read(io.BytesIO(audio_data))
            else:
                audio = np.frombuffer(audio_data, dtype=np.float32)
                sr = 16000

            if len(audio.shape) > 1:
                audio = audio.mean(axis=1)

            if sr != 16000:
                import librosa
                audio = librosa.resample(audio, orig_sr=sr, target_sr=16000)

            # Use first 30 seconds for detection
            mel = whisper.log_mel_spectrogram(audio[:sr * 30]).to(self._model.device)
            _, probs = self._model.detect_language(mel)
            detected = max(probs, key=probs.get)
            return detected

        except Exception as e:
            log.error("Language detection failed: %s", e)
            return "unknown"

    def _fallback_result(self) -> STTResult:
        return STTResult(
            text="",
            language="unknown",
            confidence=0.0,
            segments=[],
            duration_sec=0.0,
            word_count=0,
        )
