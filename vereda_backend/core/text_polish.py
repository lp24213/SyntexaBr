"""Remove artefactos típicos de LLM (markdown, símbolos estranhos) e alivia pontuação para PT-BR."""
from __future__ import annotations

import re


def strip_llm_markdown_artifacts(text: str) -> str:
    """Texto corrido para UI e PDF/Excel — sem **, `, links markdown, etc."""
    t = str(text or "")
    if not t.strip():
        return t
    # Blocos de código
    t = re.sub(r"```[\s\S]*?```", "\n", t)
    t = re.sub(r"`([^`]+)`", r"\1", t)
    # Links [texto](url) → texto
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
    # Negrito/itálico markdown (evita apagar um único * de “3 * 4”)
    t = re.sub(r"\*\*\*([^*]+)\*\*\*", r"\1", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"\1", t)
    t = re.sub(r"(?<![*\d])\*([^*\n]{2,200})\*(?![*\d])", r"\1", t)
    t = re.sub(r"__([^_]+)__", r"\1", t)
    t = re.sub(r"(?<![\d])_([^_\n]{2,200})_(?![\d])", r"\1", t)
    # Cabeçalhos #
    t = re.sub(r"(?m)^#{1,6}\s+", "", t)
    # Listas com - ou * no início da linha → marcador simples
    t = re.sub(r"(?m)^\s*[-*+]\s+", "• ", t)
    # Espaços estranhos e caracteres de controlo invisíveis
    t = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", t)
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    # Vírgulas / pontos com espaço errado antes
    t = re.sub(r"\s+,", ",", t)
    t = re.sub(r"\s+\.", ".", t)
    return t.strip()


def polish_portuguese_light(text: str) -> str:
    """Ajustes mínimos de espaçamento; acentos vêm do modelo ou fix_text_encoding."""
    t = strip_llm_markdown_artifacts(text)
    # Espaço antes de ? ! … em PT
    t = re.sub(r"\s+([?!…])", r"\1", t)
    t = re.sub(r"([?!])\s*([A-ZÁÉÍÓÚÂÊÔÃÕÇ])", r"\1 \2", t)
    return t
