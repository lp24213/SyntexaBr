# -*- coding: utf-8 -*-
"""Score de confiança heurístico a partir de convergência e qualidade de fontes."""
from __future__ import annotations

from typing import List, Tuple

from vereda_backend.search.schemas import SearchResult
from vereda_backend.search.source_ranker import score_result


def score_from_results(results: List[SearchResult]) -> Tuple[float, str]:
    if not results:
        return 0.35, "Poucas fontes recuperadas; resposta baseada sobretudo no modelo interno."
    scores = [score_result(r) for r in results[:8]]
    avg = sum(scores) / max(1, len(scores))
    spread = max(scores) - min(scores) if len(scores) > 1 else 0.0
    adjusted = avg * (0.92 + 0.08 * min(1.0, len(results) / 6.0))
    if spread < 0.08 and len(results) >= 3:
        adjusted = min(1.0, adjusted + 0.04)
    note = (
        "Fontes públicas ranqueadas e usadas como contexto; confirme dados críticos em fontes primárias."
        if len(results) >= 2
        else "Contexto web limitado; verifique fatos sensíveis em fonte oficial."
    )
    return max(0.0, min(1.0, adjusted)), note
