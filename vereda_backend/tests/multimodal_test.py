"""Testes de regressão multimodal (sem rede)."""
from __future__ import annotations

from vereda_backend.docs.pdf_builder import build_pdf_bytes
from vereda_backend.docs.xlsx_builder import build_xlsx_bytes
from vereda_backend.multimodal.file_detector import detect_kind


def test_detect_pdf():
    assert detect_kind("x.pdf", b"%PDF-1.4\n") == "pdf"


def test_detect_png():
    assert detect_kind("a.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 20) == "image"


def test_pdf_builder_starts_with_pdf():
    raw = build_pdf_bytes(
        "Título",
        [{"heading": "Intro", "body": "Corpo do texto."}],
        subtitle="Sub",
    )
    assert raw[:4] == b"%PDF"


def test_xlsx_signature():
    raw = build_xlsx_bytes("Plan1", [["A", "B"], [1, 2]], header=True)
    assert raw[:2] == b"PK"
