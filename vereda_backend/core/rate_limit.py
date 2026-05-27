"""
Rate limiting utilitário — usa Redis quando disponível (distribuído),
com fallback transparente para dicionário thread-safe em memória.

Uso:
    from vereda_backend.core.rate_limit import RateLimiter, get_client_ip

    _login_limiter = RateLimiter(max_calls=10, window_seconds=60)

    @router.post("/login")
    def login(request: Request, ...):
        _login_limiter.check(get_client_ip(request))
        ...
"""

import logging
import os
import threading
import time
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from fastapi import HTTPException, Request, status

from vereda_backend.core.redis_app import get_redis

logger = logging.getLogger(__name__)

TEST_KEY: str | None = os.environ.get("SYNTEXA_TEST_KEY") or None


def is_test_request(request: Request) -> bool:
    """Retorna True se o header X-Syntexa-Test-Key corresponder à env var SYNTEXA_TEST_KEY."""
    if not TEST_KEY:
        return False
    header = request.headers.get("x-syntexa-test-key")
    return header == TEST_KEY


def get_client_ip(request: Request) -> str:
    """Extrai o IP real do cliente, respeitando proxies Cloudflare e Nginx."""
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip.strip()
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    if request.client:
        return request.client.host
    return "unknown"


class _InMemoryRateLimiter:
    """Rate limiter em memória com sliding window e eviction automática (fallback)."""

    def __init__(self, max_calls: int, window_seconds: int, max_keys: int = 10_000):
        self._max_calls = max_calls
        self._window = timedelta(seconds=window_seconds)
        self._max_keys = max_keys
        self._store: OrderedDict[str, List[datetime]] = OrderedDict()
        self._lock = threading.Lock()

    def _evict(self) -> None:
        while len(self._store) > self._max_keys:
            self._store.popitem(last=False)

    def is_allowed(self, key: str) -> tuple[bool, int]:
        now = datetime.utcnow()
        window_start = now - self._window
        with self._lock:
            history = self._store.get(key, [])
            history = [ts for ts in history if ts >= window_start]
            if len(history) >= self._max_calls:
                self._store[key] = history
                self._store.move_to_end(key)
                return False, 0
            history.append(now)
            self._store[key] = history
            self._store.move_to_end(key)
            self._evict()
            return True, self._max_calls - len(history)


class _RedisRateLimiter:
    """Rate limiter distribuído usando Redis sorted sets (sliding window)."""

    def __init__(self, max_calls: int, window_seconds: int, prefix: str = "rl"):
        self._max_calls = max_calls
        self._window = window_seconds
        self._prefix = prefix

    def is_allowed(self, key: str) -> tuple[bool, int]:
        redis_client = get_redis()
        if redis_client is None:
            return True, self._max_calls
        redis_key = f"{self._prefix}:{key}"
        now = time.time()
        window_start = now - self._window
        pipe = redis_client.pipeline()
        pipe.zremrangebyscore(redis_key, 0, window_start)
        pipe.zcard(redis_key)
        pipe.zadd(redis_key, {str(now): now})
        pipe.expire(redis_key, self._window)
        try:
            _, current_count, _, _ = pipe.execute()
        except Exception as exc:
            logger.warning("Redis rate limit falhou (%s); permitindo passagem.", exc)
            return True, self._max_calls
        if current_count >= self._max_calls:
            return False, 0
        return True, self._max_calls - current_count


class RateLimiter:
    """
    Rate limiter híbrido: Redis (distribuído) quando disponível,
    fallback para memória thread-safe caso contrário.

    Parâmetros:
        max_calls:       número máximo de chamadas permitidas na janela
        window_seconds:  duração da janela em segundos
        max_keys:        tamanho máximo do cache em memória (fallback)
    """

    def __init__(self, max_calls: int, window_seconds: int, max_keys: int = 10_000):
        self._max_calls = max_calls
        self._window_seconds = window_seconds
        self._redis_limiter = _RedisRateLimiter(max_calls, window_seconds)
        self._memory_limiter = _InMemoryRateLimiter(max_calls, window_seconds, max_keys)
        self._window = timedelta(seconds=window_seconds)

    def is_allowed(self, key: str) -> tuple[bool, int]:
        """
        Verifica se a chave está dentro do limite.
        Retorna (allowed: bool, remaining: int).
        """
        # Tentar Redis primeiro
        redis_client = get_redis()
        if redis_client is not None:
            try:
                return self._redis_limiter.is_allowed(key)
            except Exception as exc:
                logger.warning("Redis rate limit erro (%s); fallback memória.", exc)
        return self._memory_limiter.is_allowed(key)

    def check(self, key: str, detail: str | None = None) -> None:
        """Levanta HTTP 429 se o limite foi excedido."""
        allowed, remaining = self.is_allowed(key)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=detail or f"Muitas tentativas. Aguarde antes de tentar novamente.",
                headers={"Retry-After": str(int(self._window.total_seconds()))},
            )


# ─── Limitadores pré-configurados por domínio ────────────────────────────────

# Login: 10 tentativas por minuto por IP — previne brute force
login_limiter = RateLimiter(max_calls=10, window_seconds=60)

# Registro: 5 cadastros por hora por IP — previne spam de contas
register_limiter = RateLimiter(max_calls=5, window_seconds=3600)

# Reset de senha: 5 pedidos por hora por IP — previne abuso
password_reset_limiter = RateLimiter(max_calls=5, window_seconds=3600)

# Verificação de e-mail: 10 tentativas por 5 minutos — previne força bruta de código
verify_email_limiter = RateLimiter(max_calls=10, window_seconds=300)

# Chat público (24h / IP): limites altos para conversa fluir; anónimos mais baixos que logados.
_public_chat_anon = RateLimiter(max_calls=5000, window_seconds=86400, max_keys=50_000)
_public_chat_auth = RateLimiter(max_calls=20000, window_seconds=86400, max_keys=80_000)
_public_chat_gov = RateLimiter(max_calls=50000, window_seconds=86400, max_keys=20_000)


def check_public_chat_tier(ip: str, user: Optional[object], *, detail: Optional[str] = None) -> None:
    """
    Prioriza contas logadas e plano governo sem exigir hardware novo (apenas limites distintos).
    """
    msg = detail or (
        "Limite diário de mensagens atingido. Crie uma conta ou aguarde para continuar."
    )
    if user is not None:
        plan = (getattr(user, "subscription_plan", "") or "").lower()
        if plan in ("gov", "government") or getattr(user, "is_admin", False):
            _public_chat_gov.check(ip, detail=msg)
        else:
            _public_chat_auth.check(ip, detail=msg)
    else:
        _public_chat_anon.check(ip, detail=msg)
