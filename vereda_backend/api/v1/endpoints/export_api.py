"""API de exportação de documentos (PDF, XLSX, DOCX, TXT, JSON) — sempre disponível, mesmo em gateway mode."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, Field
from starlette.responses import Response

from vereda_backend.queues.media_jobs import run_pdf_export_sync, run_xlsx_export_sync
from vereda_backend.docs.docx_builder import build_docx_bytes

router = APIRouter(prefix="/multimodal")
_log = logging.getLogger(__name__)


class PdfExportBody(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    subtitle: Optional[str] = Field(None, max_length=500)
    sections: List[Dict[str, Any]] = Field(default_factory=list)
    styled: bool = Field(default=True, description="PDF com capa, sumário e visual profissional. False = limpo, só texto.")
    include_footer: bool = Field(default=False, description="Incluir rodapé de página/data no PDF.")


class XlsxExportBody(BaseModel):
    sheet_title: str = Field(default="Dados", max_length=31)
    rows: List[List[Any]] = Field(default_factory=list)
    header: bool = True
    document_title: Optional[str] = Field(
        default=None,
        max_length=200,
        description="Faixa de título opcional no topo da folha (openpyxl).",
    )


class DocxExportBody(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    sections: List[Dict[str, Any]] = Field(default_factory=list)


class TxtExportBody(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    body: str = Field(default="", max_length=500_000)


class SmartExportBody(BaseModel):
    user_message: str = Field(..., min_length=2, max_length=12000)
    generate_audio: bool = True
    assistant_reply: str | None = Field(
        default=None,
        max_length=500_000,
        description="Última resposta do assistente no chat — usada como corpo do PDF/planilha quando o pedido é só comando de exportação.",
    )


@router.post("/export/pdf")
def multimodal_export_pdf(body: PdfExportBody) -> Response:
    try:
        raw = run_pdf_export_sync(
            body.title, body.sections, body.subtitle,
            styled=body.styled, include_footer=body.include_footer
        )
    except Exception as exc:
        _log.exception("pdf export")
        raise HTTPException(status_code=503, detail="Falha ao gerar PDF.") from exc
    fn = "".join(c for c in body.title[:60] if c.isalnum() or c in (" ", "-", "_")).strip() or "documento"
    return Response(
        content=raw,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{fn}.pdf"'},
    )


@router.post("/export/xlsx")
def multimodal_export_xlsx(body: XlsxExportBody) -> Response:
    try:
        raw = run_xlsx_export_sync(
            body.sheet_title,
            body.rows,
            body.header,
            document_title=body.document_title,
        )
    except Exception as exc:
        _log.exception("xlsx export")
        raise HTTPException(status_code=503, detail="Falha ao gerar planilha.") from exc
    st = "".join(c for c in body.sheet_title[:40] if c.isalnum() or c in (" ", "-", "_")) or "dados"
    return Response(
        content=raw,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{st}.xlsx"'},
    )


@router.post("/export/docx")
def multimodal_export_docx(body: DocxExportBody) -> Response:
    try:
        raw = build_docx_bytes(body.title, body.sections)
    except Exception as exc:
        _log.exception("docx export")
        raise HTTPException(status_code=503, detail="Falha ao gerar DOCX.") from exc
    fn = "".join(c for c in body.title[:60] if c.isalnum() or c in (" ", "-", "_")).strip() or "documento"
    return Response(
        content=raw,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{fn}.docx"'},
    )


@router.post("/export/txt")
def multimodal_export_txt(body: TxtExportBody) -> Response:
    raw = (body.body or "").encode("utf-8")
    fn = "".join(c for c in body.title[:60] if c.isalnum() or c in (" ", "-", "_")).strip() or "documento"
    return Response(
        content=raw,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{fn}.txt"'},
    )


@router.post("/json/export")
def multimodal_json_export(payload: Dict[str, Any] = Body(...)) -> Response:
    """Exporta JSON formatado como ficheiro .json (útil no chat)."""
    raw = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    return Response(
        content=raw,
        media_type="application/json; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="syntexa-export.json"'},
    )
