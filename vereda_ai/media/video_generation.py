from typing import Any


class VideoGeneration:
    """
    Interface para geração de vídeos a partir de texto.
    """

    def generate(self, prompt: str, seconds: int = 10) -> dict[str, Any]:
        return {
            "ok": True,
            "prompt": prompt,
            "duration_s": seconds,
            "url": None,
            "note": "Integre com gerador de vídeos real aqui.",
        }

