# -*- coding: utf-8 -*-
"""
Enhanced web search: caching, result ranking, optional summarization.
Backend-agnostic: pass in your web_search(query, max_results) -> list of items with .text, .source, .confidence.
"""
from typing import Any, Callable, List, Optional

from vereda_ai.cache.web_search_cache import WebSearchCache


# Default cache instance (can be overridden by backend)
_default_cache: Optional[WebSearchCache] = None


def set_web_search_cache(cache: WebSearchCache) -> None:
    global _default_cache
    _default_cache = cache


def _to_dicts(items: List[Any]) -> List[dict]:
    """Normalize to list of dicts for cache."""
    out = []
    for r in items:
        if hasattr(r, "text"):
            out.append({
                "text": getattr(r, "text", ""),
                "source": getattr(r, "source", ""),
                "confidence": getattr(r, "confidence", 1.0),
                "metadata": getattr(r, "metadata", {}) or {},
            })
        elif isinstance(r, dict):
            out.append(r)
        else:
            out.append({"text": str(r), "source": "", "confidence": 1.0, "metadata": {}})
    return out


def _from_dicts(items: List[dict], result_class: Optional[type] = None) -> List[Any]:
    """Convert cached dicts back to result_class if provided."""
    if not result_class:
        return items
    out = []
    for d in items:
        try:
            out.append(result_class(
                text=d.get("text", ""),
                source=d.get("source", ""),
                confidence=float(d.get("confidence", 1.0)),
                metadata=d.get("metadata", {}),
            ))
        except Exception:
            out.append(d)
    return out


def web_search_cached(
    query: str,
    max_results: int = 8,
    search_fn: Optional[Callable[[str, int], List[Any]]] = None,
    cache: Optional[WebSearchCache] = None,
    result_class: Optional[type] = None,
) -> List[Any]:
    """
    Run web search with cache. If search_fn is None, only cache get/set is used;
    the backend should pass search_fn=web_search (from search_architecture).
    """
    c = cache or _default_cache
    if c:
        cached = c.get(query, max_results)
        if cached is not None:
            return _from_dicts(cached, result_class)
    if not search_fn:
        return []
    results = search_fn(query, max_results)
    if c and results:
        c.set(query, _to_dicts(results), max_results)
    return results


def rank_results(
    items: List[Any],
    query_lower: str,
    key_text: Callable[[Any], str] = lambda x: getattr(x, "text", str(x)),
) -> List[Any]:
    """Simple ranking: prefer longer text and query term overlap."""
    qw = set(query_lower.split())
    def score(x):
        t = key_text(x).lower()
        tw = set(t.split())
        overlap = len(qw & tw)
        length = min(len(t), 1000) / 1000.0
        return overlap * 2.0 + length
    return sorted(items, key=score, reverse=True)


def rank_and_summarize(
    items: List[Any],
    query: str,
    max_return: int = 8,
    summarizer: Optional[Callable[[str], str]] = None,
) -> List[Any]:
    """Rank results and optionally summarize. summarizer can be LLM-based (backend provides)."""
    if not items:
        return items
    ranked = rank_results(items, query.lower())
    top = ranked[:max_return]
    if not summarizer:
        return top
    out = []
    for r in top:
        text = getattr(r, "text", str(r))
        summary = summarizer(text[:2000])
        if hasattr(r, "text"):
            r2 = type(r)(text=summary or text, source=getattr(r, "source", ""), confidence=getattr(r, "confidence", 1.0), metadata=getattr(r, "metadata", {}))
        else:
            r2 = {"text": summary or text, "source": r.get("source", ""), "confidence": r.get("confidence", 1.0), "metadata": r.get("metadata", {})}
        out.append(r2)
    return out
