"""
Controle global de concorrência para execuções de IA (Fase 3).
- Limite por usuário/IP + limite global
- Atraso maior para baixa prioridade quando o sistema está carregado
- Timeouts maiores para governo/admin
"""
from __future__ import annotations

import logging
import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from typing import Iterator, Optional, TYPE_CHECKING

from vereda_backend.core.config import settings
from vereda_backend.core.load_monitor import stress_level
from vereda_backend.core.priority import TrafficPriority, priority_for_user

if TYPE_CHECKING:
    from vereda_backend.db import models

logger = logging.getLogger(__name__)

_global_sem: Optional[threading.BoundedSemaphore] = None
_user_semaphores: "OrderedDict[str, threading.BoundedSemaphore]" = OrderedDict()
_user_lock = threading.Lock()
# Máximo de chaves distintas (user / IP) com semáforo; picos 10k+ conexões precisam de margem
_MAX_USER_KEYS = 20000


class SlotTimeoutError(RuntimeError):
    """Não foi possível obter slot de execução a tempo (servidor saturado)."""


def _global() -> threading.BoundedSemaphore:
    global _global_sem
    if _global_sem is None:
        n = max(1, int(getattr(settings, "global_max_concurrent_llm", 12) or 12))
        _global_sem = threading.BoundedSemaphore(n)
    return _global_sem


def _per_user_max() -> int:
    return max(1, int(getattr(settings, "per_user_max_concurrent_llm", 3) or 3))


def _user_key(user: Optional["models.User"], client_ip: str) -> str:
    if user is not None:
        return f"u:{user.id}"
    ip = (client_ip or "unknown").strip() or "unknown"
    return f"i:{ip}"


def _get_user_sem(key: str) -> threading.BoundedSemaphore:
    with _user_lock:
        sem = _user_semaphores.get(key)
        if sem is None:
            while len(_user_semaphores) >= _MAX_USER_KEYS:
                _user_semaphores.popitem(last=False)
            sem = threading.BoundedSemaphore(_per_user_max())
            _user_semaphores[key] = sem
        _user_semaphores.move_to_end(key)
        return sem


def _priority_backoff_sec(priority: TrafficPriority, stress: float) -> float:
    """Atraso extra para baixa prioridade quando stress alto (auto-throttling)."""
    if stress < 0.35:
        return 0.0
    base = {"PUBLIC": 0.22, "AUTH": 0.08, "GOV": 0.0}[priority.name]
    return base * stress


def _acquire_timeout_sec(priority: TrafficPriority) -> float:
    return float(
        {
            TrafficPriority.GOV: getattr(settings, "slot_timeout_gov_sec", 300.0),
            TrafficPriority.AUTH: getattr(settings, "slot_timeout_auth_sec", 120.0),
            TrafficPriority.PUBLIC: getattr(settings, "slot_timeout_public_sec", 45.0),
        }[priority]
    )


@contextmanager
def llm_execution_slot(
    user: Optional["models.User"],
    client_ip: str,
) -> Iterator[None]:
    from vereda_backend.core import load_monitor

    pr = priority_for_user(user)
    stress = load_monitor.stress_level()
    delay = _priority_backoff_sec(pr, stress)
    if delay > 0:
        time.sleep(delay)

    load_monitor.inc_active()
    g = _global()
    ukey = _user_key(user, client_ip)
    us = _get_user_sem(ukey)
    t_global = _acquire_timeout_sec(pr)
    t_user = min(t_global, max(5.0, t_global * 0.9))

    acquired_g = g.acquire(timeout=t_global)
    if not acquired_g:
        load_monitor.dec_active()
        raise SlotTimeoutError("Servidor ocupado: limite global de execuções simultâneas.")
    try:
        acquired_u = us.acquire(timeout=t_user)
        if not acquired_u:
            raise SlotTimeoutError("Servidor ocupado: limite de requisições simultâneas para este usuário/IP.")
        try:
            yield
        finally:
            us.release()
    finally:
        g.release()
        load_monitor.dec_active()


def stats() -> dict:
    g = _global()
    avail = -1
    try:
        avail = int(getattr(g, "_value", -1))
    except Exception:
        pass
    return {
        "global_llm_slots_available_approx": avail,
        "per_user_max_concurrent": _per_user_max(),
        "tracked_user_keys": len(_user_semaphores),
    }
