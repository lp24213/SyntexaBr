# -*- coding: utf-8 -*-
"""Cache for web search results. Reduces DuckDuckGo calls on repeated queries."""
import hashlib
import threading
import time
from typing import List, Optional

# Results: list of dicts with keys text, source, confidence, metadata (backend-agnostic)


class WebSearchCache:
    """In-memory TTL cache for web search results. Lightweight, no Redis required."""

    def __init__(self, ttl_seconds: int = 3600, max_entries: int = 500):
        self.ttl = ttl_seconds
        self.max_entries = max_entries
        self._cache: dict = {}
        self._lock = threading.Lock()
        self._order: List[str] = []

    def _key(self, query: str, max_results: int) -> str:
        h = hashlib.sha256((query.strip().lower() + "|" + str(max_results)).encode()).hexdigest()
        return "ws:" + h[:24]

    def get(
        self, query: str, max_results: int = 8
    ) -> Optional[List[dict]]:
        """Return cached results as list of dicts (text, source, confidence, metadata)."""
        k = self._key(query, max_results)
        with self._lock:
            entry = self._cache.get(k)
            if entry and entry[0] > time.time():
                return entry[1]
            if entry:
                del self._cache[k]
                if k in self._order:
                    self._order.remove(k)
        return None

    def set(
        self,
        query: str,
        results: List[dict],
        max_results: int = 8,
    ) -> None:
        k = self._key(query, max_results)
        expire_at = time.time() + self.ttl
        with self._lock:
            if len(self._cache) >= self.max_entries and k not in self._cache:
                while self._order and len(self._cache) >= self.max_entries:
                    old = self._order.pop(0)
                    self._cache.pop(old, None)
            self._cache[k] = (expire_at, results)
            if k not in self._order:
                self._order.append(k)
