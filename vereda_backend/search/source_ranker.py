# -*- coding: utf-8 -*-
"""Ranqueamento heurístico de fontes públicas (domínios mais confiáveis primeiro)."""
from __future__ import annotations

import re
from typing import List
from urllib.parse import urlparse

from vereda_backend.search.schemas import SearchResult

_TRUSTED_SUFFIXES = (
    ".gov.br",
    ".jus.br",
    ".edu",
    ".ac.uk",
    ".edu.br",
    "wikipedia.org",
    "wikimedia.org",
    "nih.gov",
    "who.int",
    "un.org",
)

_NEWS_HINT = re.compile(r"\b(notícia|noticia|hoje|últimas|ultimas|breaking|g1\.|folha|estadão)\b", re.I)


def _domain_trust(url: str) -> float:
    if not url or url in ("web", "news", "duckduckgo", "semantic-scholar"):
        return 0.35
    try:
        host = (urlparse(url).netloc or "").lower()
    except Exception:
        return 0.35
    if not host:
        return 0.35
    bonus = 0.0
    for suf in _TRUSTED_SUFFIXES:
        if suf in host:
            bonus += 0.22
            break
    if "wikipedia" in host:
        bonus += 0.18
    if host.endswith(".br") and "gov" in host:
        bonus += 0.12
    return min(1.0, 0.45 + bonus)


def score_result(r: SearchResult) -> float:
    base = float(r.confidence or 0.7)
    trust = _domain_trust(r.source or "")
    eng = (r.metadata or {}).get("engine") or ""
    if eng == "wikipedia":
        trust = max(trust, 0.9)
    if eng == "google_cse":
        trust = max(trust, 0.82)
    combined = 0.55 * base + 0.45 * trust
    title = (r.metadata or {}).get("title") or ""
    text = f"{title} {r.text}".lower()
    if _NEWS_HINT.search(text):
        combined *= 0.92
    return combined


def rank_and_dedupe(results: List[SearchResult], max_n: int = 10) -> List[SearchResult]:
    seen: set[str] = set()
    uniq: List[SearchResult] = []
    for r in results:
        key = (r.source or "")[:200] + "|" + (r.text or "")[:80]
        if key in seen:
            continue
        seen.add(key)
        uniq.append(r)
    uniq.sort(key=score_result, reverse=True)
    return uniq[: max(1, max_n)]
