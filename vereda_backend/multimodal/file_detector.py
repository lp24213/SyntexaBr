"""Detecção de tipo por assinatura + nome (sem confiar só no Content-Type do cliente)."""
from __future__ import annotations

import re
from typing import Literal

Kind = Literal["pdf", "image", "audio", "text", "office", "unknown"]


def detect_kind(filename: str, data: bytes) -> Kind:
    fn = (filename or "").lower()
    if data[:4] == b"%PDF":
        return "pdf"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "image"
    if data[:3] == b"\xff\xd8\xff":
        return "image"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "image"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image"
    if data[:4] == b"fLaC" or data[:3] == b"ID3" or (len(data) > 1 and data[0:2] == b"\xff\xfb"):
        return "audio"
    if data[:4] == b"RIFF" and len(data) > 12 and data[8:12] == b"WAVE":
        return "audio"
    if data[:4] == b"OggS":
        return "audio"
    if data[:2] == b"PK" and fn.endswith(".docx"):
        return "office"
    if data[:2] == b"PK" and (fn.endswith(".xlsx") or fn.endswith(".xlsm")):
        return "office"
    if fn.endswith((".txt", ".md", ".csv", ".json")):
        return "text"
    if re.search(r"\.(png|jpe?g|gif|webp|bmp|tiff?)$", fn):
        return "image"
    if re.search(r"\.(mp3|wav|ogg|flac|m4a|webm)$", fn):
        return "audio"
    if fn.endswith(".pdf"):
        return "pdf"
    return "unknown"
