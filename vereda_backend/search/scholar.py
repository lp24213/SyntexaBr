# -*- coding: utf-8 -*-
"""Semantic Scholar — API pública de busca (respeitar rate limits)."""
from __future__ import annotations

import logging
from typing import List

import requests

from vereda_backend.search.schemas import SearchResult

logger = logging.getLogger(__name__)

S2_SEARCH = "https://api.semanticscholar.org/graph/v1/paper/search"


def search_semantic_scholar(query: str, max_results: int = 4) -> List[SearchResult]:
    q = (query or "").strip()
    if not q:
        return []
    out: List[SearchResult] = []
    try:
        r = requests.get(
            S2_SEARCH,
            params={"query": q[:280], "limit": max_results, "fields": "title,abstract,url,year"},
            timeout=10,
            headers={"Accept": "application/json"},
        )
        r.raise_for_status()
        data = r.json()
        for p in data.get("data") or []:
            title = p.get("title") or ""
            abstract = (p.get("abstract") or "")[:700]
            url = p.get("url") or ""
            year = p.get("year")
            text = f"{title}" + (f" ({year})" if year else "") + (f": {abstract}" if abstract else "")
            if text.strip():
                out.append(
                    SearchResult(
                        text=text[:1100],
                        source=url or "semantic-scholar",
                        confidence=0.85,
                        metadata={"engine": "semantic_scholar", "title": title},
                    )
                )
    except Exception as exc:
        logger.debug("semantic scholar search failed: %s", exc)
    return out


def _looks_academic(query: str) -> bool:
    t = (query or "").lower()
    markers = (
        "paper",
        "artigo",
        "doi",
        "journal",
        "peer",
        "pesquisa",
        "estudo",
        "metodologia",
        "hipótese",
        "hipotese",
        "ciência",
        "ciencia",
        "pubmed",
    )
    return any(m in t for m in markers) or len(t) > 80


def maybe_scholar(query: str, max_results: int = 3) -> List[SearchResult]:
    if not _looks_academic(query):
        return []
    return search_semantic_scholar(query, max_results=max_results)
