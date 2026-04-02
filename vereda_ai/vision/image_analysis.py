from typing import Any

import numpy as np
from PIL import Image


class ImageAnalysis:
    """
    Análise básica de imagens: resolução, cores médias, etc.
    """

    def basic_stats(self, img: Image.Image) -> dict[str, Any]:
        arr = np.array(img.convert("RGB"))
        h, w, _ = arr.shape
        mean = arr.mean(axis=(0, 1)).tolist()
        return {"width": w, "height": h, "mean_rgb": mean}

