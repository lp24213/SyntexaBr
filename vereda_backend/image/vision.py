"""Análise visual local (PIL/NumPy) + metadados; descrição pesada via LLM de visão quando configurado."""
from __future__ import annotations

import io
import logging
from typing import Any, Dict, Optional

from PIL import Image

from vereda_ai.vision import ImageAnalysis
from vereda_backend.services.llm_client import describe_image

_log = logging.getLogger(__name__)
_analysis = ImageAnalysis()


def analyze_image_bytes(data: bytes, describe: bool = False) -> Dict[str, Any]:
    """Estatísticas rápidas; opcionalmente descrição via endpoint de visão (LOCAL_LLM / TGI / etc.)."""
    if not data:
        return {"ok": False, "detail": "bytes vazios"}
    try:
        img = Image.open(io.BytesIO(data))
        stats = _analysis.basic_stats(img)
    except Exception as exc:
        _log.warning("vision analyze: %s", exc)
        return {"ok": False, "detail": "imagem inválida ou corrompida"}
    out: Dict[str, Any] = {"ok": True, "stats": stats, "format": getattr(img, "format", None)}
    if describe:
        try:
            buf = io.BytesIO(data)
            buf.name = "upload.bin"
            caption = describe_image(buf, "Descreva objetos, texto visível e contexto em português, de forma objetiva.")
            if caption:
                out["description"] = caption
        except Exception as exc:
            _log.debug("describe_image skip: %s", exc)
    return out


def dominant_color_hex(data: bytes) -> Optional[str]:
    try:
        img = Image.open(io.BytesIO(data)).convert("RGB")
        img = img.resize((32, 32))
        pixels = list(img.getdata())
        r = sum(p[0] for p in pixels) // len(pixels)
        g = sum(p[1] for p in pixels) // len(pixels)
        b = sum(p[2] for p in pixels) // len(pixels)
        return f"#{r:02x}{g:02x}{b:02x}"
    except Exception:
        return None
