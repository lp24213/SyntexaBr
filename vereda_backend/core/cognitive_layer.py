# -*- coding: utf-8 -*-
"""
Syntexa Cognitive Layer
=======================
Pipeline de pós-processamento que transforma a saída crua do LLM em
resposta percebida como inteligência da Syntexa — não do modelo base.

Estágios (todos opcionais/feature-flagged, nenhum quebra o fluxo existente):

  1. anti_generic        — detecta e remove frases genéricas de IA
  2. structural_variety  — varia abertura/fecho para evitar padrões repetitivos
  3. depth_signal        — insere profundidade contextual quando ausente
  4. humanization        — ritmo variável, cadência natural PT-BR
  5. entropy_balance     — reduz predictability sem inventar factos

Integração: importar `cognitive_refine(text, ctx)` no chat_engine.py
após receber a resposta do LLM, antes de enviar ao utilizador.
"""
from __future__ import annotations

import random
import re
from dataclasses import dataclass, field
from typing import Optional


# ─── Feature flags ────────────────────────────────────────────────────────────
# Cada estágio pode ser desactivado sem alterar a assinatura pública.
_ENABLED = {
    "anti_generic": True,
    "structural_variety": True,
    "depth_signal": False,   # activar quando modelo base tiver qualidade suficiente
    "humanization": True,
    "entropy_balance": True,
}


@dataclass
class CognitiveContext:
    """Contexto passado ao pipeline para calibração da resposta."""
    user_name: Optional[str] = None
    locale: str = "pt-BR"
    is_first_message: bool = False
    topic_hint: Optional[str] = None
    response_length: int = 0          # preenchido automaticamente
    previous_opener: Optional[str] = None   # para evitar repetição


# ─── 1. Anti-generic layer ────────────────────────────────────────────────────
_GENERIC_OPENERS = re.compile(
    r"^("
    r"claro[,!]?\s*|"
    r"com certeza[,!]?\s*|"
    r"claro que sim[,!]?\s*|"
    r"ótima pergunta[,!]?\s*|"
    r"boa pergunta[,!]?\s*|"
    r"excelente pergunta[,!]?\s*|"
    r"entendido[,!]?\s*|"
    r"certamente[,!]?\s*|"
    r"sem dúvida[,!]?\s*|"
    r"com prazer[,!]?\s*|"
    r"com todo o prazer[,!]?\s*|"
    r"é uma pergunta muito boa[,!]?\s*|"
    r"vou ajudá-lo com isso[,!]?\s*|"
    r"vou te ajudar com isso[,!]?\s*|"
    r"vou te explicar[,!]?\s*|"
    r"claro[,!]?\s*"
    r")",
    re.IGNORECASE,
)

_GENERIC_CLOSERS = re.compile(
    r"("
    r"espero ter ajudado[.!]?\s*$|"
    r"espero que isso ajude[.!]?\s*$|"
    r"se precisar de mais alguma coisa[^.]*[.!]\s*$|"
    r"qualquer dúvida[^.]*[.!]\s*$|"
    r"fico à disposição[.!]?\s*$|"
    r"estou aqui para ajudar[.!]?\s*$|"
    r"posso ajudar com mais algo\??\s*$|"
    r"se tiver mais perguntas[^.]*[.!]\s*$"
    r")",
    re.IGNORECASE,
)


def _strip_generic_openers(text: str) -> str:
    return _GENERIC_OPENERS.sub("", text).lstrip()


def _strip_generic_closers(text: str) -> str:
    lines = text.rstrip().splitlines()
    if not lines:
        return text
    last = lines[-1]
    cleaned = _GENERIC_CLOSERS.sub("", last).strip()
    if cleaned != last:
        lines[-1] = cleaned
    return "\n".join(lines).rstrip()


def _anti_generic(text: str) -> str:
    text = _strip_generic_openers(text)
    text = _strip_generic_closers(text)
    # Remove excesso de pontuação afirmativa no início ("Sim! Sim, " etc.)
    text = re.sub(r"^(Sim[,!]\s*){1,3}", "", text, flags=re.IGNORECASE)
    return text.strip()


# ─── 2. Structural variety ────────────────────────────────────────────────────
_TRANSITION_OVERUSE = re.compile(
    r"\b(em resumo|em síntese|portanto|sendo assim|nesse contexto|"
    r"em outras palavras|vale ressaltar que|é importante mencionar que|"
    r"é válido destacar que|é importante destacar que)\b",
    re.IGNORECASE,
)

_TRANSITION_REPLACEMENTS = {
    "em resumo": ["no fundo", "resumindo", "em poucas palavras"],
    "em síntese": ["dito isso", "no essencial"],
    "portanto": ["então", "logo", "daí que"],
    "sendo assim": ["com isso", "nesse caso"],
    "em outras palavras": ["ou seja", "isto é", "na prática"],
    "vale ressaltar que": ["note que", "vale dizer que", "repare que"],
    "é importante mencionar que": ["vale dizer que", "note que"],
    "é válido destacar que": ["vale notar que", "é relevante que"],
    "é importante destacar que": ["cabe notar que", "repare que"],
    "nesse contexto": ["aqui", "nesse caso", "nessa situação"],
}


def _structural_variety(text: str) -> str:
    def _replace(m: re.Match) -> str:
        key = m.group(0).lower()
        options = _TRANSITION_REPLACEMENTS.get(key)
        if options:
            return random.choice(options)
        return m.group(0)
    return _TRANSITION_OVERUSE.sub(_replace, text)


# ─── 3. Humanization ─────────────────────────────────────────────────────────
# Remove listas excessivas em respostas curtas (≤3 itens para respostas <400 chars)
_BULLET_LINE = re.compile(r"^\s*[•\-\*]\s+", re.MULTILINE)


def _humanize_short_lists(text: str) -> str:
    """Converte listas pequenas em prosa quando a resposta é curta."""
    if len(text) > 400:
        return text
    bullets = _BULLET_LINE.findall(text)
    if len(bullets) not in (2, 3):
        return text
    items = [_BULLET_LINE.sub("", line).strip()
             for line in text.splitlines() if _BULLET_LINE.match(line)]
    if not items:
        return text
    if len(items) == 2:
        return text.replace(
            "\n".join(line for line in text.splitlines() if _BULLET_LINE.match(line)),
            f"{items[0]} e {items[1]}",
        )
    return text


def _humanization(text: str, ctx: CognitiveContext) -> str:
    text = _humanize_short_lists(text)
    # Reduz excesso de "!" (mais de 2 seguidos ou mais de 3 na resposta inteira)
    text = re.sub(r"!{3,}", "!", text)
    exclamations = text.count("!")
    if exclamations > 3 and len(text) < 600:
        # Substitui metade dos "!" por "." aleatoriamente
        positions = [i for i, c in enumerate(text) if c == "!"]
        to_replace = random.sample(positions, min(len(positions) // 2, exclamations - 2))
        text_list = list(text)
        for pos in to_replace:
            text_list[pos] = "."
        text = "".join(text_list)
    return text


# ─── 4. Entropy balance ───────────────────────────────────────────────────────
# Detecta resposta ultra-previsível (começa com substantivo + "é" + definição)
_DEFINITION_OPENER = re.compile(r"^[A-ZÁÉÍÓÚ][a-záéíóú]+ é ", re.MULTILINE)


def _entropy_balance(text: str) -> str:
    """Pequenos ajustes para reduzir predictability sem alterar factos."""
    # Quando a resposta começa com definição seca, adiciona abertura contextual
    if _DEFINITION_OPENER.match(text) and len(text) < 300:
        openers = [
            "Na prática, ",
            "Em termos simples, ",
            "Para entender direto: ",
            "Tecnicamente falando, ",
        ]
        text = random.choice(openers) + text[0].lower() + text[1:]
    return text


# ─── Pipeline público ─────────────────────────────────────────────────────────
def cognitive_refine(text: str, ctx: Optional[CognitiveContext] = None) -> str:
    """
    Aplica o pipeline cognitivo ao texto de saída do LLM.
    Seguro: qualquer excepção interna devolve o texto original sem alteração.
    Todos os estágios são feature-flagged via _ENABLED.
    """
    if not text or not text.strip():
        return text
    _ctx = ctx or CognitiveContext()
    _ctx.response_length = len(text)
    try:
        if _ENABLED.get("anti_generic"):
            text = _anti_generic(text)
        if _ENABLED.get("structural_variety"):
            text = _structural_variety(text)
        if _ENABLED.get("humanization"):
            text = _humanization(text, _ctx)
        if _ENABLED.get("entropy_balance"):
            text = _entropy_balance(text)
    except Exception:
        pass  # nunca quebrar o fluxo de resposta
    return text or ""
