"""
SYNTEXA STT (Speech-to-Text)
==============================
Motor de transcrição de áudio local.
Interface soberana; usa Whisper local quando disponível.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SyntexaSTT:
    """
    Motor STT soberano da Syntexa.
    Tenta carregar whisper localmente; caso contrário, levanta erro claro.
    """

    def __init__(self, model_size: str = "base", device: Optional[str] = None):
        self.model_size = model_size
        self.device = device or ("cuda" if self._cuda_available() else "cpu")
        self._model: Optional[object] = None

    def _cuda_available(self) -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except Exception:
            return False

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        try:
            import whisper
            logger.info("[SyntexaSTT] Carregando Whisper %s em %s", self.model_size, self.device)
            self._model = whisper.load_model(self.model_size, device=self.device)
        except ImportError as exc:
            raise RuntimeError(
                "Whisper não instalado. Instale: pip install openai-whisper"
            ) from exc

    def transcribe(self, audio_path: str | Path, language: Optional[str] = "pt") -> str:
        self._ensure_loaded()
        audio_path = Path(audio_path)
        if not audio_path.is_file():
            raise FileNotFoundError(f"Arquivo de áudio não encontrado: {audio_path}")
        result = self._model.transcribe(str(audio_path), language=language)  # type: ignore[attr-defined]
        return str(result.get("text", "")).strip()

    def transcribe_bytes(self, audio_bytes: bytes, language: Optional[str] = "pt") -> str:
        """Transcreve a partir de bytes (ex: buffer de microfone)."""
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            f.write(audio_bytes)
            tmp = f.name
        try:
            return self.transcribe(tmp, language=language)
        finally:
            Path(tmp).unlink(missing_ok=True)
