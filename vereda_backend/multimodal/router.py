"""Orquestração multimodal: camada rápida (metadados/OCR) vs pesada (visão LLM)."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict

from vereda_backend.image.ocr import extract_text
from vereda_backend.image.vision import analyze_image_bytes
from vereda_backend.multimodal.file_detector import Kind, detect_kind
from vereda_backend.audio.stt import transcribe_bytes

_log = logging.getLogger(__name__)


def process_bytes(
    filename: str,
    data: bytes,
    content_type: str = "",
    deep: bool = False,
) -> Dict[str, Any]:
    kind: Kind = detect_kind(filename, data)
    base: Dict[str, Any] = {
        "ok": True,
        "detected_kind": kind,
        "filename": filename,
        "size": len(data),
        "content_type": content_type,
    }

    if kind == "pdf":
        ocr = extract_text(data, kind="pdf")
        base["ocr"] = ocr
        return base

    if kind == "image":
        vis = analyze_image_bytes(data, describe=deep)
        base["vision"] = vis
        ocr = extract_text(data, kind="image")
        base["ocr"] = ocr
        return base

    if kind == "audio":
        stt = transcribe_bytes(data, filename=filename, content_type=content_type)
        base["transcription"] = stt
        return base

    if kind == "text":
        try:
            txt = data.decode("utf-8")
        except Exception:
            txt = data.decode("utf-8", errors="replace")
        preview = txt[:8000]
        base["text_preview"] = preview
        base["chars"] = len(txt)
        return base

    if kind == "office":
        base["ok"] = True
        base["note"] = "Documento Office detectado; extração completa requer pipeline dedicado (DOCX/XLSX)."
        return base

    base["ok"] = False
    base["detail"] = "Tipo não classificado; envie PDF, imagem, áudio ou texto."
    return base


def process_json_payload(raw: str) -> Dict[str, Any]:
    try:
        return json.loads(raw)
    except Exception as exc:
        _log.debug("json payload: %s", exc)
        return {}
