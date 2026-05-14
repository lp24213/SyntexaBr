"""OCR com lazy loading."""
from __future__ import annotations

import base64
import io
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from worker.core.engines import ocr_image

router = APIRouter()


class OCRRequest(BaseModel):
    image_base64: str
    language: str = "por"


@router.post("/ocr")
def optical_character_recognition(req: OCRRequest) -> dict[str, Any]:
    try:
        image_bytes = base64.b64decode(req.image_base64)
        result = ocr_image(io.BytesIO(image_bytes))
        return {"ok": True, **result}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"OCR failed: {exc}")
