"""
VEREDA / SYNTEXA — Audio Engine
================================
Engine de áudio com:
- Audio classification
- Feature extraction
- Music analysis
- Sound event detection
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False

log = logging.getLogger(__name__)


@dataclass
class AudioResult:
    duration_sec: float
    sample_rate: int
    channels: int
    features: Dict[str, Any]
    classification: str
    confidence: float


class AudioEngine:
    """
    Engine de análise de áudio.
    """

    def __init__(self):
        self._check_dependencies()

    def _check_dependencies(self) -> None:
        if not LIBROSA_AVAILABLE:
            log.warning("Librosa não disponível — análise de áudio limitada")

    # ── AUDIO ANALYSIS ───────────────────────────────────────
    def analyze(self, audio_data: bytes, sample_rate: int = 22050) -> AudioResult:
        """
        Analisa áudio e extrai features.
        """
        if not LIBROSA_AVAILABLE:
            return self._fallback_result()

        try:
            import numpy as np

            # Converte bytes para numpy array
            y = np.frombuffer(audio_data, dtype=np.float32)
            if len(y) == 0:
                return self._fallback_result()

            duration = len(y) / sample_rate

            # Feature extraction
            features = self._extract_features(y, sample_rate)

            # Simple classification
            classification = self._classify_audio(features)

            return AudioResult(
                duration_sec=round(duration, 2),
                sample_rate=sample_rate,
                channels=1 if len(y.shape) == 1 else y.shape[0],
                features=features,
                classification=classification["label"],
                confidence=classification["confidence"],
            )

        except Exception as e:
            log.error("Audio analysis failed: %s", e)
            return self._fallback_result()

    def _extract_features(self, y: Any, sr: int) -> Dict[str, Any]:
        """Extrai features de áudio."""
        try:
            import numpy as np

            features = {}

            # Spectral features
            features["spectral_centroid"] = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))
            features["spectral_rolloff"] = float(np.mean(librosa.feature.spectral_rolloff(y=y, sr=sr)))
            features["zero_crossing_rate"] = float(np.mean(librosa.feature.zero_crossing_rate(y)))

            # Rhythm
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            features["tempo"] = float(tempo)

            # MFCCs
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            features["mfcc_mean"] = [float(x) for x in np.mean(mfccs, axis=1)]
            features["mfcc_std"] = [float(x) for x in np.std(mfccs, axis=1)]

            # Energy
            features["rms_energy"] = float(np.mean(librosa.feature.rms(y=y)))

            return features

        except Exception as e:
            log.warning("Feature extraction failed: %s", e)
            return {}

    def _classify_audio(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Classifica áudio baseado em features."""
        if not features:
            return {"label": "unknown", "confidence": 0.0}

        tempo = features.get("tempo", 0)
        zcr = features.get("zero_crossing_rate", 0)
        rms = features.get("rms_energy", 0)

        # Heurísticas simples
        if tempo > 80 and rms > 0.1:
            return {"label": "music", "confidence": 0.7}
        elif zcr > 0.1:
            return {"label": "speech", "confidence": 0.6}
        elif rms < 0.01:
            return {"label": "silence", "confidence": 0.9}
        else:
            return {"label": "ambient", "confidence": 0.5}

    # ── MUSIC ANALYSIS ───────────────────────────────────────
    def analyze_music(self, audio_data: bytes, sample_rate: int = 22050) -> Dict[str, Any]:
        """Análise específica para música."""
        if not LIBROSA_AVAILABLE:
            return {"error": "Librosa não disponível"}

        try:
            import numpy as np
            y = np.frombuffer(audio_data, dtype=np.float32)

            # Tempo
            tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sample_rate)

            # Chroma (harmonia)
            chroma = librosa.feature.chroma_stft(y=y, sr=sample_rate)
            chroma_mean = np.mean(chroma, axis=1)

            # Detect key
            key = self._detect_key(chroma_mean)

            return {
                "tempo_bpm": float(tempo),
                "beat_count": len(beat_frames),
                "key": key,
                "duration_sec": round(len(y) / sample_rate, 2),
            }

        except Exception as e:
            log.error("Music analysis failed: %s", e)
            return {"error": str(e)}

    def _detect_key(self, chroma_mean: Any) -> str:
        """Detecta tonalidade baseada em chroma features."""
        keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        if len(chroma_mean) >= 12:
            max_idx = int(__import__('numpy').argmax(chroma_mean[:12]))
            return keys[max_idx]
        return "unknown"

    def _fallback_result(self) -> AudioResult:
        return AudioResult(
            duration_sec=0.0,
            sample_rate=0,
            channels=0,
            features={},
            classification="unavailable",
            confidence=0.0,
        )
