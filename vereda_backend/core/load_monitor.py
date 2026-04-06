"""Monitor leve de carga: CPU, RAM, requisições ativas (sem serviço extra)."""
from __future__ import annotations

import threading
from typing import Any, Dict, Optional

try:
    import psutil
except ImportError:
    psutil = None

from vereda_backend.core.config import settings

_lock = threading.Lock()
_active_requests = 0


def inc_active() -> None:
    global _active_requests
    with _lock:
        _active_requests += 1


def dec_active() -> None:
    global _active_requests
    with _lock:
        _active_requests = max(0, _active_requests - 1)


def active_requests() -> int:
    with _lock:
        return _active_requests


def cpu_percent() -> float:
    if not psutil:
        return 0.0
    try:
        return float(psutil.cpu_percent(interval=None))
    except Exception:
        return 0.0


def memory_percent() -> float:
    if not psutil:
        return 0.0
    try:
        return float(psutil.virtual_memory().percent)
    except Exception:
        return 0.0


def stress_level() -> float:
    """
    0 = folga, 1 = muito carregado.
    Combina CPU e RAM (sem custo de amostragem longa).
    """
    w_cpu = float(getattr(settings, "load_stress_weight_cpu", 0.55) or 0.55)
    w_mem = float(getattr(settings, "load_stress_weight_mem", 0.45) or 0.45)
    c = cpu_percent() / 100.0
    m = memory_percent() / 100.0
    return max(0.0, min(1.0, w_cpu * c + w_mem * m))


def stress_to_output_scale(stress: float) -> float:
    """Reduz tokens de saída quando stress alto (degradação suave)."""
    lo = float(getattr(settings, "load_degrade_scale_min", 0.52) or 0.52)
    return max(lo, 1.0 - 0.48 * stress)


def should_offload_public_to_queue(stress: float) -> bool:
    """Só desvia anônimos para fila quando CPU/RAM altos e Redis disponível."""
    thr = float(getattr(settings, "load_queue_stress_threshold", 0.78) or 0.78)
    return stress >= thr


def snapshot() -> Dict[str, Any]:
    """Snapshot para /admin (sem PII)."""
    out: Dict[str, Any] = {
        "active_requests": active_requests(),
        "cpu_percent": round(cpu_percent(), 1),
        "memory_percent": round(memory_percent(), 1),
        "stress_level": round(stress_level(), 3),
        "psutil": psutil is not None,
    }
    q = _approx_arq_queue_depth()
    if q is not None:
        out["arq_queue_depth_approx"] = q
    return out


def _approx_arq_queue_depth() -> Optional[int]:
    from vereda_backend.core.redis_app import get_redis

    r = get_redis()
    if not r:
        return None
    try:
        # ARQ 0.26: lista de jobs pendentes
        n = r.llen("arq:queue")
        return int(n) if n is not None else None
    except Exception:
        return None
