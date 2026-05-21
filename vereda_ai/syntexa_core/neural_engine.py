"""
VEREDA / SYNTEXA — Neural Engine (LEGADO / DESCONTINUADO)
===========================================================
Este módulo foi DESCONTINUADO na V39. A Syntexa não utiliza mais
modelos de terceiros (Qwen, Llama, Phi, etc.).

Use a Foundation Model própria:
  from vereda_ai.syntexa_core.foundation_runtime import foundation_generate
"""
from __future__ import annotations

import logging
from typing import Any, Iterator, Optional

logger = logging.getLogger(__name__)


def is_neural_available() -> bool:
    """Sempre retorna False — modelos de terceiros foram removidos."""
    return False


class NeuralEngine:
    """Engine legado removido. Levanta erro ao tentar inicializar."""

    def __init__(self, *args, **kwargs):
        raise RuntimeError(
            "[Syntexa V39] NeuralEngine descontinuado. "
            "Use a Foundation Model própria: foundation_generate()"
        )

    def generate(self, *args, **kwargs):
        raise RuntimeError("NeuralEngine descontinuado.")

    def generate_stream(self, *args, **kwargs):
        raise RuntimeError("NeuralEngine descontinuado.")


def neural_generate(*args, **kwargs):
    raise RuntimeError(
        "[Syntexa V39] neural_generate descontinuado. Use foundation_generate()"
    )


def neural_generate_stream(*args, **kwargs):
    raise RuntimeError(
        "[Syntexa V39] neural_generate_stream descontinuado. Use foundation_generate_stream()"
    )


# stubs para não quebrar imports antigos
_transformers = None
_torch = None
LARGE_MODELS = []

# FIM DO ARQUIVO — NeuralEngine descontinuado (V39)
