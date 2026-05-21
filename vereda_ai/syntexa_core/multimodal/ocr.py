"""
SYNTEXA OCR
===========
Reconhecimento óptico de caracteres local.
Backends: easyocr (preferido), pytesseract (fallback).
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SyntexaOCR:
    """
    Motor OCR soberano da Syntexa.
    """

    def __init__(self, lang: str = "pt", gpu: bool = True):
        self.lang = lang
        self.gpu = gpu
        self._reader: Optional[object] = None
        self._backend: Optional[str] = None

    def _ensure_loaded(self) -> None:
        if self._reader is not None:
            return
        try:
            import easyocr
            logger.info("[SyntexaOCR] Carregando EasyOCR (lang=%s, gpu=%s)", self.lang, self.gpu)
            self._reader = easyocr.Reader([self.lang], gpu=self.gpu)
            self._backend = "easyocr"
            return
        except Exception as exc:
            logger.debug("EasyOCR não disponível: %s", exc)

        try:
            import pytesseract
            from PIL import Image
            logger.info("[SyntexaOCR] Usando Pytesseract fallback")
            self._reader = pytesseract
            self._backend = "tesseract"
            return
        except Exception as exc:
            logger.debug("Pytesseract não disponível: %s", exc)

        raise RuntimeError(
            "Nenhum backend OCR disponível. Instale: pip install easyocr  (ou pytesseract)"
        )

    def extract_text(self, image_path: str | Path) -> str:
        self._ensure_loaded()
        image_path = Path(image_path)
        if not image_path.is_file():
            raise FileNotFoundError(f"Imagem não encontrada: {image_path}")

        if self._backend == "easyocr":
            results = self._reader.readtext(str(image_path), detail=0)  # type: ignore[attr-defined]
            return "\n".join(results)
        elif self._backend == "tesseract":
            from PIL import Image
            img = Image.open(image_path)
            return self._reader.image_to_string(img, lang=self.lang)  # type: ignore[attr-defined]
        else:
            raise RuntimeError(f"Backend OCR desconhecido: {self._backend}")

    def extract_text_from_pdf(self, pdf_path: str | Path, dpi: int = 300) -> str:
        """Extrai texto de PDF via conversão de página para imagem + OCR."""
        from pdf2image import convert_from_path
        pages = convert_from_path(str(pdf_path), dpi=dpi)
        texts: list[str] = []
        for i, page in enumerate(pages):
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                page.save(f.name)
                texts.append(self.extract_text(f.name))
                Path(f.name).unlink(missing_ok=True)
        return "\n\n".join(texts)
