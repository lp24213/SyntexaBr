"""
Rate limiting utilitário — sem dependências externas (sem Redis).
Usa um dicionário thread-safe em memória com eviction LRU.

Uso:
    from vereda_backend.core.rate_limit import RateLimiter, get_client_ip

    _login_limiter = RateLimiter(max_calls=10, window_seconds=60)

    @router.post("/login")
    def login(request: Request, ...):
        _login_limiter.check(get_client_ip(request))
        ...
"""

import threading
from collections import OrderedDict
from datetime import datetime, timedelta
from typing import Dict, List

from fastapi import HTTPException, Request, status


def get_client_ip(request: Request) -> str:
    """Extrai o IP real do cliente, respeitando proxies Cloudflare e Nginx."""
    cf_ip = request.headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip.strip()
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


class RateLimiter:
    """
    Rate limiter em memória com sliding window e eviction automática.

    Parâmetros:
        max_calls:       número máximo de chamadas permitidas na janela
        window_seconds:  duração da janela em segundos
        max_keys:        tamanho máximo do cache (evita crescimento ilimitado)
    """

    def __init__(self, max_calls: int, window_seconds: int, max_keys: int = 10_000):
        self._max_calls = max_calls
        self._window = timedelta(seconds=window_seconds)
        self._max_keys = max_keys
        # OrderedDict para LRU eviction: chave → lista de timestamps
        self._store: OrderedDict[str, List[datetime]] = OrderedDict()
        self._lock = threading.Lock()

    def _evict(self) -> None:
        """Remove entradas mais antigas quando o cache excede max_keys."""
        while len(self._store) > self._max_keys:
            self._store.popitem(last=False)

    def is_allowed(self, key: str) -> tuple[bool, int]:
        """
        Verifica se a chave está dentro do limite.
        Retorna (allowed: bool, remaining: int).
        """
        now = datetime.utcnow()
        window_start = now - self._window
        with self._lock:
            history = self._store.get(key, [])
            # Slide the window
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
