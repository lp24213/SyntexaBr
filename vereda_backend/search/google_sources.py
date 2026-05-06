# -*- coding: utf-8 -*-
"""
Google Custom Search JSON API (oficial).
Defina GOOGLE_API_KEY + GOOGLE_CSE_ID (CX) no ambiente; sem isso retorna lista vazia.
https://developers.google.com/custom-search/v1/overview
"""
from __future__ import annotations

import logging
import os
from typing import List
from urllib.parse import urlencode

import requests

from vereda_backend.search.schemas import SearchResult

logger = logging.getLogger(__name__)


def search_google_custom(query: str, max_results: int = 5) -> List[SearchResult]:
    key = (os.environ.get("GOOGLE_API_KEY") or os.environ.get("GOOGLE_CSE_API_KEY") or "").strip()
    cx = (os.environ.get("GOOGLE_CSE_ID") or os.environ.get("GOOGLE_CX") or "").strip()
    if not key or not cx or not (query or "").strip():
        return []
    out: List[SearchResult] = []
    try:
        params = urlencode(
            {
                "key": key,
                "cx": cx,
                "q": query.strip(),
                "num": min(10, max(1, max_results)),
            }
        )
        url = f"https://www.googleapis.com/customsearch/v1?{params}"
        resp = requests.get(url, timeout=8)
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("items") or []:
            title = item.get("title") or ""
            snippet = item.get("snippet") or ""
            link = item.get("link") or ""
            text = f"{title}: {snippet}".strip()
            if text:
                out.append(
                    SearchResult(
                        text=text[:900],
                        source=link or "google-cse",
                        confidence=0.88,
                        metadata={"engine": "google_cse", "title": title},
                    )
                )
            if len(out) >= max_results:
                break
    except Exception as exc:
        logger.debug("Google CSE search failed: %s", exc)
    return out
