from __future__ import annotations

import threading
import time
from typing import Any

from vereda_backend.core.config import settings
from vereda_backend.services import events


def _get_ai_settings():
    from vereda_ai.core.config import settings as _s
    return _s


def _runtime_readiness_report():
    from vereda_ai.syntexa_core.runtime_model import runtime_readiness_report
    return runtime_readiness_report()

_LOCK = threading.Lock()
_STARTED = False
_THREAD: threading.Thread | None = None
_STOP_EVENT = threading.Event()
_LAST_ALERT_AT = 0.0
_SNAPSHOT: dict[str, Any] = {
    "ready": False,
    "checked_at": 0.0,
    "detail": "watchdog não executado",
    "active_model": None,
}


def _should_enforce() -> bool:
    env_backend = str(getattr(settings, "environment", "local") or "local").lower()
    ai_settings = _get_ai_settings()
    env_ai = str(getattr(ai_settings, "environment", "local") or "local").lower()
    strict = bool(getattr(ai_settings, "own_model_strict_no_fallback", False))
    return strict or env_backend in {"prod", "production"} or env_ai in {"prod", "production"}


def _is_syntexa_native_default() -> bool:
    return str(getattr(settings, "default_llm", "") or "").strip().lower() == "syntexa_native"


def _check_once() -> dict[str, Any]:
    report = _runtime_readiness_report()
    checks = report.get("checks") or []
    detail = ""
    if checks and isinstance(checks, list):
        last = checks[-1]
        if isinstance(last, dict):
            detail = str(last.get("detail") or "")
    snap = {
        "ready": bool(report.get("ready", False)),
        "checked_at": time.time(),
        "detail": detail or "sem detalhe",
        "active_model": report.get("active_model"),
    }
    with _LOCK:
        _SNAPSHOT.update(snap)
    return snap


def _maybe_alert_failure(snap: dict[str, Any]) -> None:
    global _LAST_ALERT_AT
    if not _should_enforce() or not _is_syntexa_native_default():
        return
    if bool(snap.get("ready")):
        return
    now = time.time()
    cooldown = max(30.0, float(getattr(settings, "chat_runtime_alert_cooldown_sec", 120.0) or 120.0))
    with _LOCK:
        if now - _LAST_ALERT_AT < cooldown:
            return
        _LAST_ALERT_AT = now
    events.notify_chat_runtime_unavailable(
        error_text=str(snap.get("detail") or "runtime readiness check failed"),
        user=None,
        provider="syntexa_native",
    )


def _loop() -> None:
    interval = max(10.0, float(getattr(settings, "own_model_watchdog_interval_sec", 60.0) or 60.0))
    while not _STOP_EVENT.is_set():
        try:
            snap = _check_once()
            _maybe_alert_failure(snap)
        except Exception:
            pass
        _STOP_EVENT.wait(interval)


def start_runtime_watchdog() -> None:
    global _STARTED, _THREAD
    if not bool(getattr(settings, "own_model_watchdog_enabled", True)):
        return
    with _LOCK:
        if _STARTED:
            return
        _STARTED = True
    _STOP_EVENT.clear()
    _THREAD = threading.Thread(target=_loop, name="syntexa-runtime-watchdog", daemon=True)
    _THREAD.start()


def get_runtime_watchdog_snapshot() -> dict[str, Any]:
    with _LOCK:
        checked_at = float(_SNAPSHOT.get("checked_at", 0.0) or 0.0)
        snapshot_copy = dict(_SNAPSHOT)
    if checked_at <= 0:
        try:
            return _check_once()
        except Exception:
            return snapshot_copy
    return snapshot_copy
