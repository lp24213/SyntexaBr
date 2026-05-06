# -*- coding: utf-8 -*-
"""Notícias via DuckDuckGo News (sem API key)."""
from __future__ import annotations

import logging
from typing import List

from vereda_backend.search.schemas import SearchResult

logger = logging.getLogger(__name__)


def search_news_ddg(query: str, max_results: int = 4) -> List[SearchResult]:
    if not (query or "").strip():
        return []
    out: List[SearchResult] = []
    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            for r in ddgs.news(query, max_results=max_results):
                title = r.get("title") or ""
                body = r.get("body") or r.get("snippet") or ""
                src = r.get("url") or r.get("source") or ""
                text = f"{title}: {body}".strip()
                if text:
                    out.append(
                        SearchResult(
                            text=text[:850],
                            source=str(src) or "news",
                            confidence=0.78,
                            metadata={"engine": "ddg_news", "title": title},
                        )
                    )
                if len(out) >= max_results:
                    break
    except Exception as exc:
        logger.debug("ddg news failed: %s", exc)
    return out
