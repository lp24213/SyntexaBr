# -*- coding: utf-8 -*-
"""
Orquestra classificação leve, busca híbrida, citações e confiança para o chat.
O LLM final continua sendo o motor registado em `llm_engine` (syntexa_native por padrão).
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Tuple

from vereda_backend.core.config import settings
from vereda_backend.core.confidence_score import score_from_results
from vereda_backend.rag.citations import format_search_results_as_citations
from vereda_backend.search.hybrid import hybrid_public_search, hybrid_public_search_fast
from vereda_backend.search.source_ranker import rank_and_dedupe
from vereda_backend.search.schemas import SearchResult

_TOPIC_PATTERNS = (
    ("juridico", re.compile(r"\b(lei|art\.|artigo|stf|stj|jurisprud|processo|mpf|constitui)\w*", re.I)),
    ("ciencia", re.compile(r"\b(ciência|ciencia|paper|doi|hipótese|hipotese|ensaio clínico)\w*", re.I)),
    ("governo", re.compile(r"\b(governo|ministério|ministerio|prefeit|senado|câmara|camara)\w*", re.I)),
    ("educacao", re.compile(r"\b(escola|enem|universidade|curso|professor|aluno)\w*", re.I)),
    ("seguranca", re.compile(r"\b(vulnerabilidade|cve|pentest|malware|phishing|lgpd)\w*", re.I)),
)


_STOP_Q = frozenset(
    {
        "qual", "quais", "quem", "onde", "quando", "como", "por", "que", "para",
        "uma", "uns", "com", "sobre", "dos", "das", "pelo", "pela", "the",
        "what", "how", "why", "when", "which", "who", "esse", "essa", "isso", "aqui",
        "meu", "minha", "muito", "mais",
    }
)


def _focus_search_query(q: str) -> str:
    """Reduz ruído da pergunta para segunda passagem de busca (sem hardcodar tópicos)."""
    raw = (q or "").strip()
    if len(raw) < 6:
        return raw
    words = [
        w
        for w in re.findall(r"[\wàáâãéêíóôõúçÀÁÂÃÉÊÍÓÔÕÚÇ]+", raw, re.I)
        if len(w) > 2 and w.lower() not in _STOP_Q
    ]
    return " ".join(words[:14]) if words else raw[:140]


def classify_topic(user_text: str) -> str:
    t = (user_text or "").strip()
    if not t:
        return "geral"
    for name, rx in _TOPIC_PATTERNS:
        if rx.search(t):
            return name
    return "geral"


@dataclass
class AugmentedWeb:
    web_text: str
    citations_block: str
    confidence: float
    confidence_note: str
    topic: str


def build_augmented_web_context(
    user_query: str, *, max_results: int = 8, fast: bool = True
) -> AugmentedWeb:
    topic = classify_topic(user_query)
    q0 = (user_query or "").strip()
    hard_cap = max(8, int(getattr(settings, "chat_web_augment_max_results_cap", 28) or 28))
    cap = max(1, min(int(max_results), hard_cap))
    fast_low = max(1, int(getattr(settings, "chat_web_fast_max_total", 6) or 6))
    fast_high = max(fast_low, int(getattr(settings, "chat_web_fast_max_total_deep", 16) or 16))
    # Chat «profundo» pede web_max ≥14; aí relaxamos o teto do caminho rápido.
    deep_style = int(max_results) >= 14
    fast_budget = fast_high if deep_style else fast_low
    if fast:
        results = hybrid_public_search_fast(q0, max_total=min(cap, fast_budget))
    else:
        results = hybrid_public_search(q0, max_total=cap)
    text_len = sum(len((r.text or "")) for r in results)
    # Segunda passagem só no modo completo (evita ~2× latência no chat).
    if not fast and (len(results) < 3 or text_len < 450):
        alt = _focus_search_query(q0)
        if alt and alt.lower() != q0.lower():
            more = hybrid_public_search(alt, max_total=cap)
            results = rank_and_dedupe(results + more, max_n=cap)
    if deep_style:
        text_ceiling = int(getattr(settings, "chat_web_augment_text_chars_deep", 22000) or 22000)
    else:
        text_ceiling = int(getattr(settings, "chat_web_augment_text_chars", 12000) or 12000)
    text_ceiling = max(4000, text_ceiling)
    web_text = "\n".join(r.text for r in results if getattr(r, "text", None))[:text_ceiling]
    citations = format_search_results_as_citations(results)
    conf, note = score_from_results(results)
    return AugmentedWeb(
        web_text=web_text,
        citations_block=citations,
        confidence=conf,
        confidence_note=note,
        topic=topic,
    )


def confidence_prompt_line(confidence: float, note: str, topic: str) -> str:
    pct = max(0.0, min(1.0, confidence)) * 100.0
    return (
        f"Metadados internos (não copiar literalmente na resposta salvo o usuário pedir): "
        f"tema≈{topic}; confiança contextual estimada {pct:.0f}%. {note}"
    )
