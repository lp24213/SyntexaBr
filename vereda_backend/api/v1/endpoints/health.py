"""
Health: compatível com clientes antigos (status + service) e relatório estendido (uptime, serviços).
Não remove campos existentes; apenas acrescenta informação operacional.
"""
from __future__ import annotations

import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from sqlalchemy import text

from vereda_backend.core.config import settings
from vereda_backend.core.prom_metrics import render_metrics_text
from vereda_backend.core.redis_app import get_redis
from vereda_backend.core.runtime_watchdog import get_runtime_watchdog_snapshot
from vereda_backend.db.session import engine

router = APIRouter()

_START_MONOTONIC = time.monotonic()


def _mask_llm_for_public(llm: Dict[str, Any]) -> Dict[str, Any]:
    """Health é público: não expor URL de gateway nem rótulos de fornecedor externos."""
    out = {k: v for k, v in llm.items() if k != "checked"}
    prov = out.get("provider")
    if prov is not None and str(prov).strip() and str(prov).strip().lower() != "syntexa":
        out["provider"] = "syntexa"
    return out


def _uptime_seconds() -> float:
    return round(time.monotonic() - _START_MONOTONIC, 2)


def _service_database() -> Dict[str, Any]:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "up"}
    except Exception as exc:
        return {"status": "down", "error": str(exc)[:200]}


def _service_redis() -> Dict[str, Any]:
    url = (getattr(settings, "redis_url", None) or "").strip()
    if not url:
        return {"status": "not_configured"}
    r = get_redis()
    if not r:
        return {"status": "down", "note": "configured but unreachable"}
    try:
        r.ping()
        return {"status": "up"}
    except Exception as exc:
        return {"status": "down", "error": str(exc)[:120]}


def _service_llm() -> Dict[str, Any]:
    # Usa o cliente LLM para checar disponibilidade do endpoint preferido.
    try:
        from vereda_backend.services.llm_client import ping_llm

        return ping_llm()
    except Exception as exc:
        return {"status": "down", "error": str(exc)[:120]}


@router.get("/health")
def health_check():
    """
    Sempre responde (não remove o endpoint). Campos legados: status, service.
    Acrescenta: uptime_seconds, timestamp_utc, healthy, services.
    """
    db = _service_database()
    redis = _service_redis()
    llm = _mask_llm_for_public(_service_llm())

    db_ok = db.get("status") == "up"
    overall_ok = db_ok

    # `status` permanece "ok" enquanto o processo responde (compatível com checks antigos).
    # `ready` / `healthy` indicam se o stack está utilizável (ex.: DB).
    payload: Dict[str, Any] = {
        "status": "ok",
        "service": "vereda-ai",
        "ready": overall_ok,
        "healthy": overall_ok,
        "uptime_seconds": _uptime_seconds(),
        "timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "services": {
            "database": db,
            "redis": redis,
            "llm": llm,
        },
    }
    return payload


@router.get("/metrics", response_class=PlainTextResponse)
def prometheus_metrics() -> str:
    snap = get_runtime_watchdog_snapshot()
    ready = 1 if bool(snap.get("ready", False)) else 0
    strict = 1 if bool(getattr(settings, "chat_strict_real_providers", True)) else 0
    checked_at = float(snap.get("checked_at", 0.0) or 0.0)
    return render_metrics_text(
        runtime_ready=ready,
        strict_no_fallback=strict,
        last_check_unix=checked_at,
    )
