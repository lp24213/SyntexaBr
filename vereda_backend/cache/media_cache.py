"""Cache de artefatos multimodais (hash do conteúdo) — Redis quando disponível."""
from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Optional

from vereda_backend.core.config import settings
from vereda_backend.core.redis_app import get_redis

_log = logging.getLogger(__name__)
_PREFIX = "syntexa:media:"


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def cache_key(kind: str, data: bytes, extra: str = "") -> str:
    return f"{kind}:{_digest(data)}:{hashlib.sha256(extra.encode()).hexdigest()[:16]}"


def get_cached(key: str) -> Optional[dict]:
    r = get_redis()
    if not r:
        return None
    try:
        raw = r.get(_PREFIX + key)
        if raw:
            return json.loads(raw)
    except Exception as exc:
        _log.debug("media_cache get: %s", exc)
    return None


def set_cached(key: str, value: dict, ttl_sec: Optional[int] = None) -> None:
    r = get_redis()
    if not r:
        return
    ttl = ttl_sec if ttl_sec is not None else int(getattr(settings, "redis_chat_cache_ttl_sec", 120) or 120)
    try:
        r.setex(_PREFIX + key, max(30, ttl), json.dumps(value, ensure_ascii=False))
    except Exception as exc:
        _log.debug("media_cache set: %s", exc)
