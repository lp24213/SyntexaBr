# -*- coding: utf-8 -*-
"""Formatação de citações a partir de resultados de busca ranqueados."""
from __future__ import annotations

from typing import List

from vereda_backend.search.schemas import SearchResult


def format_search_results_as_citations(results: List[SearchResult], max_items: int = 8) -> str:
    lines: List[str] = []
    for i, r in enumerate(results[:max_items], start=1):
        title = (r.metadata or {}).get("title") or ""
        src = (r.source or "").strip() or "fonte"
        eng = (r.metadata or {}).get("engine") or ""
        head = f"[{i}]"
        if eng:
            head += f" ({eng})"
        if title:
            head += f" {title}"
        lines.append(f"{head}\n   URL/ref: {src}")
    return "\n".join(lines) if lines else ""
