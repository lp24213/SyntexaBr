# -*- coding: utf-8 -*-
"""Busca textual via DuckDuckGo (biblioteca duckduckgo-search; sem API key)."""
from __future__ import annotations

import logging
from typing import List

from vereda_backend.search.schemas import SearchResult

logger = logging.getLogger(__name__)


def search_duckduckgo(query: str, max_results: int = 6) -> List[SearchResult]:
    if not (query or "").strip():
        return []
    out: List[SearchResult] = []
    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                title = r.get("title") or ""
                body = r.get("body") or r.get("snippet") or ""
                href = r.get("href") or ""
                text = f"{title}: {body}".strip()
                if text:
                    out.append(
                        SearchResult(
                            text=text[:900],
                            source=href or "duckduckgo",
                            confidence=0.82,
                            metadata={"engine": "duckduckgo", "title": title},
                        )
                    )
                if len(out) >= max_results:
                    break
    except Exception as exc:
        logger.debug("duckduckgo search failed: %s", exc)
    return out
