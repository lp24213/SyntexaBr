from typing import Any, Dict

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from PIL import Image

from vereda_backend.core.security import get_current_admin
from vereda_ai.vision import ImageAnalysis


router = APIRouter(prefix="/vision")
image_analysis = ImageAnalysis()


@router.post("/image/basic")
async def vision_image_basic(
    file: UploadFile = File(...),
    _: Any = Depends(get_current_admin),
) -> Dict[str, Any]:
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Envie um arquivo de imagem.")

    img = Image.open(file.file)
    stats = image_analysis.basic_stats(img)
    return {"ok": True, "stats": stats}

