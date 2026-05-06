"""Extração de texto: PDF (pypdf), imagens (Tesseract opcional ou visão LLM como fallback)."""
from __future__ import annotations

import io
import logging
from typing import Any, Dict, Literal, Optional

from vereda_backend.services.llm_client import describe_image

_log = logging.getLogger(__name__)


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    parts: list[str] = []
    for page in reader.pages:
        try:
            t = page.extract_text() or ""
        except Exception:
            t = ""
        if t.strip():
            parts.append(t)
    return "\n\n".join(parts).strip()


def _tesseract_image(data: bytes) -> Optional[str]:
    try:
        import pytesseract
        from PIL import Image
    except Exception:
        return None
    try:
        img = Image.open(io.BytesIO(data))
        return (pytesseract.image_to_string(img, lang="por+eng") or "").strip() or None
    except Exception as exc:
        _log.debug("tesseract: %s", exc)
        return None


def _vision_ocr_fallback(data: bytes) -> str:
    buf = io.BytesIO(data)
    buf.name = "ocr.png"
    prompt = (
        "Transcreva todo o texto visível na imagem, preservando parágrafos. "
        "Se não houver texto, responda apenas: (sem texto legível)."
    )
    return (describe_image(buf, prompt) or "").strip()


def extract_text(
    data: bytes,
    kind: Literal["auto", "pdf", "image"] = "auto",
) -> Dict[str, Any]:
    """
    Retorna texto extraído e o método usado (auditoria / telemetria).
    """
    if not data:
        return {"ok": False, "detail": "vazio", "text": "", "method": None}

    if kind == "pdf" or (kind == "auto" and data[:4] == b"%PDF"):
        try:
            txt = _pdf_text(data)
            return {"ok": True, "text": txt, "method": "pypdf", "chars": len(txt)}
        except Exception as exc:
            _log.warning("pypdf falhou: %s", exc)
            return {"ok": False, "detail": str(exc), "text": "", "method": "pypdf"}

    if kind == "image" or kind == "auto":
        ts = _tesseract_image(data)
        if ts:
            return {"ok": True, "text": ts, "method": "tesseract", "chars": len(ts)}
        vision_txt = _vision_ocr_fallback(data)
        if vision_txt and "(sem texto legível)" not in vision_txt.lower():
            return {"ok": True, "text": vision_txt, "method": "vision_llm", "chars": len(vision_txt)}
        return {
            "ok": True,
            "text": vision_txt,
            "method": "vision_llm",
            "chars": len(vision_txt),
            "note": "OCR local avançado indisponível neste instante; resultado fornecido pelo núcleo visual Syntexa.",
        }

    return {"ok": False, "detail": "tipo não suportado", "text": "", "method": None}
