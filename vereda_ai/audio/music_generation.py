from typing import Any


class MusicGeneration:
    """
    Interface para modelos de geração de música / áudio.
    """

    def generate(self, prompt: str, duration_s: int = 30) -> dict[str, Any]:
        return {
            "ok": True,
            "prompt": prompt,
            "duration_s": duration_s,
            "url": None,
            "note": "Integre aqui seu modelo de geração musical real.",
        }

