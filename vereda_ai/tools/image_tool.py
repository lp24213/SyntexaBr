# -*- coding: utf-8 -*-
"""Análise básica de imagem. Offline."""
from typing import Any, Dict, Optional

from vereda_ai.tools.base_tool import BaseTool

try:
    from PIL import Image
    import io
    _PIL_AVAILABLE = True
except ImportError:
    _PIL_AVAILABLE = False


class ImageTool(BaseTool):
    name = "image"

    def available(self) -> bool:
        return _PIL_AVAILABLE

    def run(
        self,
        image_data: Optional[bytes] = None,
        path: Optional[str] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        if not _PIL_AVAILABLE:
            return {"ok": False, "error": "PIL não instalado."}
        if not image_data and not path:
            return {"ok": False, "error": "Forneça image_data ou path."}
        try:
            if image_data:
                img = Image.open(io.BytesIO(image_data))
            else:
                img = Image.open(path)
            img = img.convert("RGB")
            w, h = img.size
            pixels = list(img.getdata())
            n = len(pixels)
            r = sum(p[0] for p in pixels) / n
            g = sum(p[1] for p in pixels) / n
            b = sum(p[2] for p in pixels) / n
            return {
                "ok": True,
                "width": w,
                "height": h,
                "format": img.format,
                "mean_rgb": {"r": round(r, 2), "g": round(g, 2), "b": round(b, 2)},
            }
        except Exception as e:
            return {"ok": False, "error": str(e)}
