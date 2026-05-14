"""
VEREDA / SYNTEXA — OCR Engine
==============================
Engine de OCR com:
- Text extraction
- Layout preservation
- Multi-language support
- Table detection
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

try:
    import pytesseract
    from PIL import Image
    PYTESSERACT_AVAILABLE = True
except ImportError:
    PYTESSERACT_AVAILABLE = False

log = logging.getLogger(__name__)


@dataclass
class OcrResult:
    text: str
    blocks: List[Dict[str, Any]]
    language: str
    confidence: float
    word_count: int
    has_tables: bool


class OCREngine:
    """
    Engine de OCR para extração de texto de imagens e PDFs.
    """

    def __init__(self, default_language: str = "por"):
        self.default_language = default_language
        self._check_tesseract()

    def _check_tesseract(self) -> None:
        if PYTESSERACT_AVAILABLE:
            try:
                version = pytesseract.get_tesseract_version()
                log.info("Tesseract OCR available: %s", version)
            except Exception as e:
                log.warning("Tesseract not available: %s", e)

    # ── TEXT EXTRACTION ──────────────────────────────────────
    def extract_text(self, image_data: bytes, language: Optional[str] = None) -> OcrResult:
        """
        Extrai texto de imagem.
        """
        if not PYTESSERACT_AVAILABLE:
            return self._fallback_result()

        try:
            img = Image.open(__import__('io').BytesIO(image_data))
            lang = language or self.default_language

            # OCR com dados de layout
            data = pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DICT)

            text_lines = []
            blocks = []
            current_block = {"text": [], "confidence": [], "bbox": None}

            for i in range(len(data["text"])):
                word = data["text"][i].strip()
                if not word:
                    continue

                conf = int(data["conf"][i])
                if conf > 0:
                    text_lines.append(word)
                    current_block["text"].append(word)
                    current_block["confidence"].append(conf)

            full_text = "\n".join(text_lines)

            # Detect tables
            has_tables = self._detect_tables(img)

            # Calculate confidence
            confidences = [int(data["conf"][i]) for i in range(len(data["text"])) if data["text"][i].strip()]
            avg_confidence = sum(confidences) / max(len(confidences), 1) if confidences else 0

            return OcrResult(
                text=full_text,
                blocks=blocks,
                language=lang,
                confidence=avg_confidence / 100.0,
                word_count=len(text_lines),
                has_tables=has_tables,
            )

        except Exception as e:
            log.error("OCR failed: %s", e)
            return self._fallback_result()

    def extract_from_pdf_page(self, pdf_data: bytes, page_number: int = 0) -> OcrResult:
        """Extrai texto de página de PDF."""
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(stream=pdf_data, filetype="pdf")
            if page_number >= len(doc):
                return self._fallback_result()

            page = doc[page_number]
            pix = page.get_pixmap(dpi=300)
            img_data = pix.tobytes("png")
            return self.extract_text(img_data)
        except Exception as e:
            log.error("PDF OCR failed: %s", e)
            return self._fallback_result()

    # ── TABLE DETECTION ──────────────────────────────────────
    def _detect_tables(self, img: Any) -> bool:
        """Detecta presença de tabelas na imagem."""
        try:
            import cv2
            import numpy as np

            # Converte para OpenCV
            img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)

            # Detecta linhas
            edges = cv2.Canny(gray, 50, 150)
            lines = cv2.HoughLinesP(edges, 1, np.pi/180, 100, minLineLength=100, maxLineGap=10)

            if lines is not None and len(lines) > 10:
                return True
        except Exception:
            pass
        return False

    # ── LAYOUT PRESERVATION ──────────────────────────────────
    def extract_with_layout(self, image_data: bytes) -> Dict[str, Any]:
        """Extrai texto preservando layout."""
        if not PYTESSERACT_AVAILABLE:
            return {"error": "Tesseract not available"}

        try:
            img = Image.open(__import__('io').BytesIO(image_data))
            html = pytesseract.image_to_pdf_or_hocr(img, extension="hocr")
            return {
                "format": "hocr",
                "content": html.decode('utf-8') if isinstance(html, bytes) else html,
            }
        except Exception as e:
            log.error("Layout OCR failed: %s", e)
            return {"error": str(e)}

    # ── MULTI-LANGUAGE ───────────────────────────────────────
    def detect_language(self, text: str) -> str:
        """Detecta idioma do texto."""
        # Simple heuristic
        if any(c in text for c in "áéíóúãõç"):
            return "por"
        if any(c in text for c in "áéíóúñü"):
            return "spa"
        if any(ord(c) > 0x4E00 for c in text):
            return "chi_sim"
        return "eng"

    def _fallback_result(self) -> OcrResult:
        return OcrResult(
            text="OCR não disponível. Instale pytesseract e Pillow.",
            blocks=[],
            language=self.default_language,
            confidence=0.0,
            word_count=0,
            has_tables=False,
        )
