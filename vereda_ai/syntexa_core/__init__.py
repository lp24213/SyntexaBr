"""Núcleo proprietário Syntexa (Fase 1): NLP híbrido sem APIs de modelos de terceiros."""

from vereda_ai.syntexa_core.hybrid_engine import generate_reply, native_embed
from vereda_ai.syntexa_core.model_registry import get_registry

__all__ = ["generate_reply", "native_embed", "get_registry"]
