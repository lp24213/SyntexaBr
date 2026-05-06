# -*- coding: utf-8 -*-
"""
Agrega buscas de fontes públicas permitidas (DDG, Wikipedia, notícias, Scholar condicional, Google CSE opcional).
Não implementa scraping agressivo de mecanismos com ToS restritivos.
"""
from __future__ import annotations

import logging
from typing import List

from vereda_backend.search.duckduckgo import search_duckduckgo
from vereda_backend.search.google_sources import search_google_custom
from vereda_backend.search.news_fetcher import search_news_ddg
from vereda_backend.search.schemas import SearchResult
from vereda_backend.search.scholar import maybe_scholar
from vereda_backend.search.source_ranker import rank_and_dedupe
from vereda_backend.search.wiki import search_wikipedia
from vereda_backend.search.yahoo import search_yahoo

logger = logging.getLogger(__name__)


def hybrid_public_search_fast(query: str, max_total: int = 6) -> List[SearchResult]:
    """
    Caminho rápido para o chat: só DDG + Wikipedia (sem notícias/CSE/Yahoo/Scholar em série).
    Latência típica muito menor que `hybrid_public_search` completo.
    """
    q = (query or "").strip()
    if not q:
        return []
    merged: List[SearchResult] = []
    try:
        merged.extend(search_duckduckgo(q, max_results=min(4, max_total)))
        merged.extend(search_wikipedia(q, max_results=min(3, max_total)))
    except Exception as exc:
        logger.debug("hybrid_public_search_fast partial failure: %s", exc)
    ranked = rank_and_dedupe(merged, max_n=max_total)
    return ranked


def hybrid_public_search(query: str, max_total: int = 10) -> List[SearchResult]:
    q = (query or "").strip()
    if not q:
        return []
    merged: List[SearchResult] = []
    try:
        merged.extend(search_duckduckgo(q, max_results=min(6, max_total)))
        merged.extend(search_wikipedia(q, max_results=2))
        merged.extend(search_news_ddg(q, max_results=min(4, max_total)))
        merged.extend(maybe_scholar(q, max_results=3))
        merged.extend(search_google_custom(q, max_results=min(5, max_total)))
        merged.extend(search_yahoo(q, max_results=2))
    except Exception as exc:
        logger.debug("hybrid_public_search partial failure: %s", exc)
    ranked = rank_and_dedupe(merged, max_n=max_total)
    return ranked
