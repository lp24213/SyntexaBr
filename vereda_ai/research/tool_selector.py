# -*- coding: utf-8 -*-
"""
Tool selection layer: decides which tools to use for a query (web, vector, arxiv, math, crypto, quantum).
Designed for lightweight CPU; uses keyword/heuristic selection (no extra LLM call).
"""
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

from vereda_ai.router.prompt_router import RouteCategory


class ResearchTool(str, Enum):
    NONE = "none"
    WEB = "web"
    VECTOR = "vector"
    ARXIV = "arxiv"
    MATH = "math"
    CRYPTO = "crypto"
    QUANTUM = "quantum"


# Keywords that suggest using each tool (lowercase).
_TOOL_KEYWORDS: Dict[ResearchTool, List[str]] = {
    ResearchTool.WEB: [
        "buscar na web", "pesquisar na internet", "notícia", "atual", "hoje",
        "consultar", "busca web", "google", "o que está acontecendo",
    ],
    ResearchTool.VECTOR: [
        "documento", "base de conhecimento", "o que já sabemos", "memória",
        "conforme o documento", "no texto", "no arquivo",
    ],
    ResearchTool.ARXIV: [
        "paper", "artigo científico", "arxiv", "publicação", "pesquisa científica",
        "estudo publicado", "literatura", "abstract", "abstracts",
    ],
    ResearchTool.MATH: [
        "calcule", "quanto é", "raiz", "equação", "derivada", "integral",
        "matriz", "vetor", "álgebra", "probabilidade", "estatística",
        "teoria dos números", "primo", "módulo",
    ],
    ResearchTool.CRYPTO: [
        "rsa", "criptografia", "criptográfico", "cripto", "criptomoeda",
        "chave pública", "hash", "assinatura", "criptografia quântica",
        "curva elíptica", "ecc", "post-quantum",
    ],
    ResearchTool.QUANTUM: [
        "qubit", "quantum", "quântico", "porta quântica", "circuito quântico",
        "simulação quântica", "qiskit", "superposição",
    ],
}


class ToolSelector:
    """
    Selects which tools to invoke for a given query. Heuristic-based to avoid extra LLM calls.
    """

    def __init__(self) -> None:
        self._keywords = _TOOL_KEYWORDS

    def select(self, prompt: str) -> List[ResearchTool]:
        """Return list of tools to try, in order of relevance."""
        if not prompt or not prompt.strip():
            return [ResearchTool.NONE]
        text = prompt.lower().strip()
        selected = []
        for tool, keywords in self._keywords.items():
            if any(kw in text for kw in keywords):
                selected.append(tool)
        if not selected:
            return [ResearchTool.NONE]
        return selected

    def select_with_router(self, prompt: str) -> Tuple[List[ResearchTool], RouteCategory]:
        """Combine with existing PromptRouter category for compatibility."""
        from vereda_ai.router.prompt_router import PromptRouter
        router = PromptRouter()
        category = router.route(prompt)
        tools = self.select(prompt)
        return tools, category
