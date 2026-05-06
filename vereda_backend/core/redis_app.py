"""Cliente Redis síncrono (cache + sinais). Opcional: sem REDIS_URL retorna None."""
from __future__ import annotations

import logging
from typing import Optional

import redis

from vereda_backend.core.config import settings

logger = logging.getLogger(__name__)

_client: Optional[redis.Redis] = None


def get_redis() -> Optional[redis.Redis]:
    """Singleton lazy; None se REDIS_URL não configurada."""
    global _client
    url = (getattr(settings, "redis_url", None) or "").strip()
    if not url:
        return None
    if _client is None:
        try:
            _client = redis.from_url(
                url,
                decode_responses=True,
                socket_connect_timeout=5.0,
                socket_keepalive=True,
                health_check_interval=30,
            )
            _client.ping()
            logger.info("Redis conectado para cache/filas.")
        except Exception as exc:
            logger.warning("Redis indisponível (%s). Cache/fila desativados até reconectar.", exc)
            return None
    return _client
