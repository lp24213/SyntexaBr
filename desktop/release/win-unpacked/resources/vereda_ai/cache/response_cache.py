# -*- coding: utf-8 -*-
"""Cache de respostas com TTL. Fallback em memoria."""
import hashlib
import threading
import time
from typing import Optional

class ResponseCache:
    def __init__(self, ttl_seconds: int = 300, redis_url: Optional[str] = None):
        self.ttl = ttl_seconds
        self._memory = {}
        self._lock = threading.Lock()

    def _key(self, prompt: str, user_id: str = "") -> str:
        h = hashlib.sha256((prompt.strip().lower() + "|" + user_id).encode()).hexdigest()
        return "syntexa:" + h[:32]

    def get(self, prompt: str, user_id: str = "") -> Optional[str]:
        k = self._key(prompt, user_id)
        with self._lock:
            entry = self._memory.get(k)
            if entry and entry[0] > time.time():
                return entry[1]
            if entry:
                del self._memory[k]
        return None

    def set(self, prompt: str, response: str, user_id: str = "") -> None:
        k = self._key(prompt, user_id)
        expire_at = time.time() + self.ttl
        with self._lock:
            self._memory[k] = (expire_at, response)
