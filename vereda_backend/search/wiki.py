# -*- coding: utf-8 -*-
"""Wikipedia (API REST + opensearch) — uso permitido para resumos e títulos."""
from __future__ import annotations

import logging
from typing import List
from urllib.parse import quote

import requests

from vereda_backend.search.schemas import SearchResult

logger = logging.getLogger(__name__)

def search_wikipedia(query: str, max_results: int = 3, lang: str = "pt") -> List[SearchResult]:
    q = (query or "").strip()
    if not q:
        return []
    wiki_api = f"https://{lang}.wikipedia.org/w/api.php"
    wiki_rest = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary"
    out: List[SearchResult] = []
    try:
        r = requests.get(
            wiki_api,
            params={
                "action": "opensearch",
                "search": q[:200],
                "limit": max_results,
                "namespace": 0,
                "format": "json",
            },
            timeout=6,
        )
        r.raise_for_status()
        data = r.json()
        titles = data[1] if len(data) > 1 else []
        for title in titles[:max_results]:
            if not title:
                continue
            safe = quote(title.replace(" ", "_"), safe="")
            sr = requests.get(f"{wiki_rest}/{safe}", timeout=6)
            if sr.status_code != 200:
                continue
            js = sr.json()
            extract = (js.get("extract") or "")[:1200]
            src = js.get("content_urls", {}).get("desktop", {}).get("page") or ""
            if extract:
                out.append(
                    SearchResult(
                        text=f"Wikipedia ({title}): {extract}",
                        source=src or "wikipedia",
                        confidence=0.92,
                        metadata={"engine": "wikipedia", "title": title},
                    )
                )
    except Exception as exc:
        logger.debug("wikipedia search failed: %s", exc)
    return out
