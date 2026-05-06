"""Geração e download de ficheiros (.ods nativo, etc.)."""
from __future__ import annotations

import re
from typing import Any, List

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from vereda_backend.services.file_generators.ods_generator import generate_ods
from vereda_backend.services.file_generators.storage import resolve_generated_path, save_generated_bytes

router = APIRouter()


class OdsGenerateBody(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    headers: List[str] = Field(default_factory=list)
    rows: List[List[Any]] = Field(default_factory=list)


def _safe_download_name(title: str) -> str:
    base = re.sub(r"[^\w\- ]+", "_", (title or "documento").strip())[:80] or "documento"
    return base.replace(" ", "_") + ".ods"


@router.post("/generate/ods")
def post_generate_ods(body: OdsGenerateBody) -> dict[str, Any]:
    """
    Gera .ods nativo (OpenDocument Spreadsheet) e devolve URL de download temporária.
    """
    try:
        payload = {
            "title": body.title,
            "headers": body.headers,
            "rows": body.rows,
        }
        raw = generate_ods(payload, _safe_download_name(body.title))
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Falha ao gerar ODS: {exc!s}") from exc

    file_id = save_generated_bytes(raw, ".ods")
    fn = _safe_download_name(body.title)
    download_url = f"/api/files/downloads/{file_id}"
    return {
        "success": True,
        "download_url": download_url,
        "file_name": fn,
        "mime_type": "application/vnd.oasis.opendocument.spreadsheet",
        "file_id": file_id,
    }


@router.get("/downloads/{file_id}")
def get_download_ods(file_id: str, name: str | None = None):
    """Serve o .ods gerado (UUID sem extensão no path)."""
    path = resolve_generated_path(file_id, ".ods")
    if path is None:
        raise HTTPException(status_code=404, detail="Ficheiro expirado ou inexistente.")
    disp = name if name and re.match(r"^[\w\-. ]+\.ods$", name) else "syntexa.ods"
    return FileResponse(
        path,
        media_type="application/vnd.oasis.opendocument.spreadsheet",
        filename=disp,
    )
