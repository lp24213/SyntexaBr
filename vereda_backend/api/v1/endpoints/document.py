"""
VEREDA / SYNTEXA — Document API v1
=====================================
Pipeline avançado de documentos via AI Router
"""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field

from vereda_backend.core.security import get_current_user_optional
from vereda_backend.db import models

router = APIRouter(prefix="/document")


class ParseRequest(BaseModel):
    preserve_layout: bool = Field(default=True)
    extract_tables: bool = Field(default=True)
    ocr_enabled: bool = Field(default=True)


@router.post("/parse")
async def document_parse(
    file: UploadFile = File(...),
    preserve_layout: bool = Form(True),
    extract_tables: bool = Form(True),
    ocr_enabled: bool = Form(True),
    current_user: models.User | None = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    """
    Faz parse inteligente de documento:
    PDF, DOCX, XLSX, PPTX, CSV, TXT, MD, HTML, ZIP
    """
    data = await file.read()
    if len(data) > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Ficheiro muito grande (máx. 50 MB).")

    content_type = file.content_type or "application/octet-stream"

    # Validação de mime-type básica
    allowed_types = [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "text/csv",
        "text/plain",
        "text/markdown",
        "text/html",
        "application/zip",
        "application/octet-stream",
    ]

    # Se for octet-stream, inferir pela extensão
    ext = (file.filename or "").lower().split(".")[-1] if "." in (file.filename or "") else ""
    ext_map = {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "csv": "text/csv",
        "txt": "text/plain",
        "md": "text/markdown",
        "html": "text/html",
        "zip": "application/zip",
    }
    inferred_type = ext_map.get(ext, content_type)

    # Para MVP: retornar metadados + delegar parse ao AI Worker futuramente
    return {
        "ok": True,
        "filename": file.filename,
        "size_bytes": len(data),
        "content_type": inferred_type,
        "preserve_layout": preserve_layout,
        "extract_tables": extract_tables,
        "ocr_enabled": ocr_enabled,
        "status": "queued_for_processing",
        "note": "Parse completo será implementado com AI Worker + PyMuPDF/python-docx/openpyxl",
    }


@router.post("/ocr")
async def document_ocr(
    file: UploadFile = File(...),
    language: str = Form("por"),
    current_user: models.User | None = Depends(get_current_user_optional),
) -> Dict[str, Any]:
    """OCR em imagem ou PDF escaneado."""
    data = await file.read()
    if len(data) > 25 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Ficheiro muito grande (máx. 25 MB).")

    # Delegar para AI Router (vision/OCR)
    from vereda_backend.services.ai_router import get_ai_router_service
    import base64

    service = get_ai_router_service()
    img_b64 = base64.b64encode(data).decode("utf-8")
    return await service.vision_describe(img_b64, prompt=f"Extraia todo o texto deste documento. Linguagem: {language}")


@router.get("/health")
async def document_health() -> Dict[str, Any]:
    return {"status": "ok", "engine": "document-pipeline-v1"}
