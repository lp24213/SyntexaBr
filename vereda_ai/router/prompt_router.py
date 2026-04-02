# -*- coding: utf-8 -*-
"""
PromptRouter: classificação heurística leve (sem LLM) para rotear perguntas.
Otimizado para baixo consumo de CPU em servidor pequeno.
"""
from enum import Enum
from typing import Tuple


class RouteCategory(str, Enum):
    MATH = "math"
    CODE = "code"
    KNOWLEDGE = "knowledge"
    VISION = "vision"
    WEB = "web"
    CRYPTO = "crypto"
    GENERAL = "general"


# Palavras-chave por categoria (lowercase). Ordem importa: primeira match vence.
_KEYWORDS: list[Tuple[RouteCategory, list[str]]] = [
    (RouteCategory.MATH, [
        "calcule", "quanto é", "raiz", "equação", "derivada", "integral",
        "matemática", "álgebra", "geometria", "trigonometria", "bhaskara",
        "fórmula", "soma", "multiplicação", "divisão", "potência", "log",
        "seno", "cosseno", "tangente", "polinômio", "matriz", "vetor",
    ]),
    (RouteCategory.CODE, [
        "código", "programar", "função", "python", "javascript", "script",
        "algoritmo", "loop", "array", "lista", "debug", "sintaxe", "api",
        "implementar", "classe", "método", "variável", "regex",
    ]),
    (RouteCategory.CRYPTO, [
        "bitcoin", "criptomoeda", "crypto", "ethereum", "preço", "cotação",
        "blockchain", "btc", "eth", "token", "defi",
    ]),
    (RouteCategory.VISION, [
        "imagem", "foto", "figura", "analisar imagem", "descrever imagem",
        "visão", "reconhecer", "detectar", "objeto na imagem",
    ]),
    (RouteCategory.WEB, [
        "buscar na web", "pesquisar na internet", "notícia", "atual",
        "hoje", "consultar", "busca web", "google",
    ]),
    (RouteCategory.KNOWLEDGE, [
        "o que é", "quem foi", "história", "conceito", "definição",
        "explicar", "como funciona", "diferença entre", "lei ", "constituição",
        "livro", "autor", "documentação",
    ]),
]


class PromptRouter:
    """
    Roteador heurístico de prompts. Não usa LLM; apenas palavras-chave e regras.
    """

    def __init__(self) -> None:
        self._keywords = _KEYWORDS

    def route(self, prompt: str) -> RouteCategory:
        """
        Retorna a categoria do prompt. Sempre retorna uma categoria válida.
        """
        if not prompt or not prompt.strip():
            return RouteCategory.GENERAL
        text = prompt.lower().strip()
        for category, keywords in self._keywords:
            for kw in keywords:
                if kw in text:
                    return category
        return RouteCategory.GENERAL

    def route_with_confidence(self, prompt: str) -> Tuple[RouteCategory, float]:
        """
        Retorna (categoria, confiança 0..1). Heurística simples: múltiplas
        palavras da mesma categoria aumentam a confiança.
        """
        if not prompt or not prompt.strip():
            return RouteCategory.GENERAL, 0.0
        text = prompt.lower().strip()
        best_category = RouteCategory.GENERAL
        best_count = 0
        for category, keywords in self._keywords:
            count = sum(1 for kw in keywords if kw in text)
            if count > best_count:
                best_count = count
                best_category = category
        confidence = min(1.0, 0.3 + best_count * 0.2) if best_count > 0 else 0.3
        return best_category, confidence
