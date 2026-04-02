# -*- coding: utf-8 -*-
"""Cache for vector retrieval results. Reduces embedding + search load."""
import hashlib
import threading
import time
from typing import Any, List, Optional


class RetrievalCache:
    """TTL cache for similarity_search results (namespace, query, top_k)."""

    def __init__(self, ttl_seconds: int = 600, max_entries: int = 300):
        self.ttl = ttl_seconds
        self.max_entries = max_entries
        self._cache: dict = {}
        self._lock = threading.Lock()
        self._order: List[str] = []

    def _key(self, namespace: str, query: str, top_k: int) -> str:
        h = hashlib.sha256(
            (namespace + "|" + query.strip().lower() + "|" + str(top_k)).encode()
        ).hexdigest()
        return "ret:" + h[:24]

    def get(
        self, namespace: str, query: str, top_k: int = 5
    ) -> Optional[List[dict[str, Any]]]:
        k = self._key(namespace, query, top_k)
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
        namespace: str,
        query: str,
        results: List[dict[str, Any]],
        top_k: int = 5,
    ) -> None:
        k = self._key(namespace, query, top_k)
        expire_at = time.time() + self.ttl
        with self._lock:
            if len(self._cache) >= self.max_entries and k not in self._cache:
                while self._order and len(self._cache) >= self.max_entries:
                    old = self._order.pop(0)
                    self._cache.pop(old, None)
            self._cache[k] = (expire_at, results)
            if k not in self._order:
                self._order.append(k)
