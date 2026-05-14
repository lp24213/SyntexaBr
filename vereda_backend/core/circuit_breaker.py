"""
VEREDA / SYNTEXA — Circuit Breaker + Failover Engine
======================================================
Failover automático: AWS GPU → Local → Queue → Retry
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine, Optional

import httpx

from vereda_backend.core.config import settings

log = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"       # Normal — passa requisições
    OPEN = "open"           # Falhou muitas vezes — rejeita rapidamente
    HALF_OPEN = "half_open" # Testando se recuperou


@dataclass
class CircuitBreaker:
    name: str
    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    half_open_max_calls: int = 3

    _state: CircuitState = field(default=CircuitState.CLOSED, repr=False)
    _failures: int = field(default=0, repr=False)
    _last_failure_time: float = field(default=0.0, repr=False)
    _half_open_calls: int = field(default=0, repr=False)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.time() - self._last_failure_time >= self.recovery_timeout:
                return CircuitState.HALF_OPEN
        return self._state

    async def call(self, coro: Coroutine) -> Any:
        async with self._lock:
            current = self.state

            if current == CircuitState.OPEN:
                raise RuntimeError(f"Circuit breaker OPEN for {self.name}")

            if current == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self.half_open_max_calls:
                    raise RuntimeError(f"Circuit breaker HALF_OPEN limit for {self.name}")
                self._half_open_calls += 1

        try:
            result = await coro
            async with self._lock:
                self._state = CircuitState.CLOSED
                self._failures = 0
                self._half_open_calls = 0
            return result
        except Exception as e:
            async with self._lock:
                self._failures += 1
                self._last_failure_time = time.time()
                if self._failures >= self.failure_threshold:
                    self._state = CircuitState.OPEN
                    log.warning("Circuit breaker OPEN for %s (%d failures)", self.name, self._failures)
            raise


class AiRouterEngine:
    """
    Roteia inferência entre AWS GPU (primário) e Local (fallback).
    Usa circuit breaker para cada backend.
    """

    def __init__(self):
        self.aws_breaker = CircuitBreaker(name="aws_gpu", failure_threshold=3, recovery_timeout=60.0)
        self.local_breaker = CircuitBreaker(name="local_ai", failure_threshold=5, recovery_timeout=30.0)
        self.timeout = httpx.Timeout(120.0, connect=10.0)
        self.client = httpx.AsyncClient(timeout=self.timeout, follow_redirects=False)

        self.aws_base = getattr(settings, "aws_base_url", None) or getattr(settings, "ai_worker_url", None)
        self.local_base = getattr(settings, "local_base_url", None) or getattr(settings, "local_ai_url", None)
        self.aws_key = getattr(settings, "ai_worker_api_key", None)
        self.local_key = getattr(settings, "local_ai_api_key", None)

    async def inference(self, endpoint: str, payload: dict, stream: bool = False) -> httpx.Response:
        """
        Tenta AWS primeiro. Se falhar, fallback para local.
        Se ambos falharem, levanta exceção (Railway deve enfileirar).
        """
        # 1. AWS GPU (primário)
        if self.aws_base:
            try:
                return await self._call_backend(
                    breaker=self.aws_breaker,
                    base_url=self.aws_base,
                    api_key=self.aws_key,
                    endpoint=endpoint,
                    payload=payload,
                    stream=stream,
                )
            except Exception as e:
                log.warning("AWS GPU failed for %s: %s", endpoint, e)

        # 2. Local AI (fallback)
        if self.local_base:
            try:
                return await self._call_backend(
                    breaker=self.local_breaker,
                    base_url=self.local_base,
                    api_key=self.local_key,
                    endpoint=endpoint,
                    payload=payload,
                    stream=stream,
                )
            except Exception as e:
                log.warning("Local AI failed for %s: %s", endpoint, e)

        raise RuntimeError("All AI backends unavailable (AWS + Local)")

    async def _call_backend(
        self,
        breaker: CircuitBreaker,
        base_url: str,
        api_key: Optional[str],
        endpoint: str,
        payload: dict,
        stream: bool,
    ) -> httpx.Response:
        url = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        async def _do_request():
            if stream:
                return await self.client.post(url, json=payload, headers=headers, timeout=None)
            return await self.client.post(url, json=payload, headers=headers)

        resp = await breaker.call(_do_request())
        return resp

    async def health_check(self, backend: str = "aws") -> dict:
        """Verifica saúde de um backend."""
        base = self.aws_base if backend == "aws" else self.local_base
        if not base:
            return {"backend": backend, "status": "not_configured"}
        try:
            r = await self.client.get(f"{base.rstrip('/')}/health", timeout=5.0)
            return {"backend": backend, "status": "ok" if r.status_code == 200 else f"error:{r.status_code}"}
        except Exception as e:
            return {"backend": backend, "status": f"unreachable:{e}"}

    async def close(self):
        await self.client.aclose()


# Singleton global
_router_engine: Optional[AiRouterEngine] = None


def get_ai_router() -> AiRouterEngine:
    global _router_engine
    if _router_engine is None:
        _router_engine = AiRouterEngine()
    return _router_engine
