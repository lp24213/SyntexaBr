"""
SYNTEXA VISION ENCODER
======================
Encoder de imagem local para understanding multimodal.
Backends: CLIP (OpenAI/laion) via transformers quando disponível,
mas interface 100% soberana e desacoplada.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class SyntexaVisionEncoder:
    """
    Encoder visual soberano da Syntexa.
    Produz embeddings de imagem para uso em RAG multimodal ou
    como entrada para modelos multimodais futuros.
    """

    def __init__(self, model_name: str = "openai/clip-vit-base-patch32", device: Optional[str] = None):
        self.model_name = model_name
        self.device = device or ("cuda" if self._cuda_available() else "cpu")
        self._processor: Optional[object] = None
        self._model: Optional[object] = None
        self._loaded = False

    def _cuda_available(self) -> bool:
        try:
            import torch
            return torch.cuda.is_available()
        except Exception:
            return False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        try:
            from transformers import CLIPProcessor, CLIPVisionModel
            logger.info("[SyntexaVision] Carregando %s em %s", self.model_name, self.device)
            self._model = CLIPVisionModel.from_pretrained(self.model_name).to(self.device)
            self._processor = CLIPProcessor.from_pretrained(self.model_name)
            self._loaded = True
        except ImportError as exc:
            raise RuntimeError(
                "transformers não instalado para vision encoder. Instale: pip install transformers"
            ) from exc

    def encode_image(self, image_path: str | Path) -> list[float]:
        """
        Codifica imagem em vetor de embedding.
        Retorna lista de floats (normalizada).
        """
        self._ensure_loaded()
        image_path = Path(image_path)
        if not image_path.is_file():
            raise FileNotFoundError(f"Imagem não encontrada: {image_path}")

        from PIL import Image
        img = Image.open(image_path).convert("RGB")
        inputs = self._processor(images=img, return_tensors="pt")  # type: ignore[attr-defined]
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with __import__("torch").no_grad():
            outputs = self._model(**inputs)  # type: ignore[attr-defined]

        vec = outputs.pooler_output[0].cpu().numpy()
        # Normaliza L2
        norm = __import__("numpy").linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def encode_images(self, image_paths: list[str | Path]) -> list[list[float]]:
        return [self.encode_image(p) for p in image_paths]
