from typing import Any


class ImageGeneration:
    """
    Interface para geração de imagens (Stable Diffusion, DALL-E, etc).
    """

    def generate(self, prompt: str, width: int = 512, height: int = 512) -> dict[str, Any]:
        return {
            "ok": True,
            "prompt": prompt,
            "size": {"width": width, "height": height},
            "url": None,
            "note": "Integre com gerador de imagens real neste ponto.",
        }

