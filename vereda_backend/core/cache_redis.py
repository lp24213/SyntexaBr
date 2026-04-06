"""Cache Redis para respostas de chat (complementa cache em memória)."""
from __future__ import annotations

import logging
from typing import Optional

from vereda_backend.core.config import settings
from vereda_backend.core.redis_app import get_redis

logger = logging.getLogger(__name__)

PREFIX = "syntexa:chat:"
SHARED_Q_PREFIX = "syntexa:chat:q:"


def cache_get(key: str) -> Optional[str]:
    r = get_redis()
    if not r:
        return None
    try:
        return r.get(PREFIX + key)
    except Exception as exc:
        logger.debug("cache_get redis: %s", exc)
        return None


def cache_set(key: str, value: str, ttl_sec: Optional[int] = None) -> None:
    r = get_redis()
    if not r:
        return
    ttl = ttl_sec if ttl_sec is not None else int(getattr(settings, "redis_chat_cache_ttl_sec", 120) or 120)
    try:
        r.setex(PREFIX + key, max(1, ttl), value)
    except Exception as exc:
        logger.debug("cache_set redis: %s", exc)


def edu_public_cache_get(digest: str) -> Optional[str]:
    """Cache para consultas públicas do tutor (chave já é hash)."""
    r = get_redis()
    if not r:
        return None
    try:
        return r.get("syntexa:edu:tutor:" + digest)
    except Exception:
        return None


def edu_public_cache_set(digest: str, value: str, ttl_sec: int = 180) -> None:
    r = get_redis()
    if not r:
        return
    try:
        r.setex("syntexa:edu:tutor:" + digest, max(30, ttl_sec), value)
    except Exception:
        pass


def shared_question_cache_get(digest: str) -> Optional[str]:
    """Respostas idênticas (pergunta normalizada) para usuários anônimos — deduplicação."""
    r = get_redis()
    if not r:
        return None
    try:
        return r.get(SHARED_Q_PREFIX + digest)
    except Exception:
        return None


def shared_question_cache_set(digest: str, value: str, ttl_sec: int = 300) -> None:
    r = get_redis()
    if not r:
        return
    try:
        r.setex(SHARED_Q_PREFIX + digest, max(30, ttl_sec), value)
    except Exception:
        pass


def compute_cache_get(key_digest: str) -> Optional[str]:
    r = get_redis()
    if not r:
        return None
    try:
        return r.get("syntexa:edu:compute:" + key_digest)
    except Exception:
        return None


def compute_cache_set(key_digest: str, value: str, ttl_sec: int = 600) -> None:
    r = get_redis()
    if not r:
        return
    try:
        r.setex("syntexa:edu:compute:" + key_digest, max(60, ttl_sec), value)
    except Exception:
        pass
