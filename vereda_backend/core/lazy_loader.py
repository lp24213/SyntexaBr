"""Lazy loader para engines de IA pesada no vereda_backend.

NENHUM modelo é carregado no import. Tudo é lazy-loaded na primeira chamada.
"""
from __future__ import annotations

import logging
import threading
from typing import Any, Callable

logger = logging.getLogger(__name__)

_registry: dict[str, Any] = {}
_locks: dict[str, threading.Lock] = {}


def lazy_load(name: str, factory: Callable[[], Any]) -> Any:
    """Carrega um singleton de IA de forma lazy e thread-safe."""
    if name in _registry:
        return _registry[name]
    lock = _locks.setdefault(name, threading.Lock())
    with lock:
        if name in _registry:
            return _registry[name]
        logger.info("Lazy loading IA engine: %s", name)
        try:
            instance = factory()
            _registry[name] = instance
            logger.info("Lazy loaded: %s OK", name)
            return instance
        except Exception as exc:
            logger.error("Lazy load FAILED for %s: %s", name, exc)
            raise


def get_or_none(name: str) -> Any | None:
    return _registry.get(name)


def reset(name: str) -> None:
    _registry.pop(name, None)
    logger.info("Reset lazy loader: %s", name)


def reset_all() -> None:
    _registry.clear()
    logger.info("Reset all lazy loaders")
