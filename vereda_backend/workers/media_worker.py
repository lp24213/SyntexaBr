"""Funções síncronas chamadas pelo worker ARQ (importadas em tasks.py)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from vereda_backend.docs.docx_builder import build_docx_bytes
from vereda_backend.docs.pdf_builder import build_pdf_bytes
from vereda_backend.docs.xlsx_builder import build_xlsx_bytes


def sync_build_pdf(title: str, sections: List[Dict[str, Any]], subtitle: Optional[str]) -> bytes:
    return build_pdf_bytes(title, sections, subtitle)


def sync_build_xlsx(
    sheet_title: str,
    rows: List[List[Any]],
    header: bool,
    document_title: Optional[str] = None,
) -> bytes:
    return build_xlsx_bytes(sheet_title, rows, header, document_title=document_title)


def sync_build_docx(title: str, sections: List[Dict[str, Any]]) -> bytes:
    return build_docx_bytes(title, sections)
