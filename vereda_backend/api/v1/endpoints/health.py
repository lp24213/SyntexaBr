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
from sqlalchemy import text

from vereda_backend.core.config import settings
from vereda_backend.core.redis_app import get_redis
from vereda_backend.db.session import engine

router = APIRouter()

_START_MONOTONIC = time.monotonic()


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


def _service_ollama() -> Dict[str, Any]:
    ep = (settings.ollama_endpoint or "").strip()
    if not ep:
        return {"status": "not_configured"}
    url = ep.rstrip("/") + "/api/tags"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=1.8) as resp:
            code = getattr(resp, "status", 200) or 200
            if 200 <= int(code) < 300:
                return {"status": "up"}
            return {"status": "degraded", "http": int(code)}
    except urllib.error.HTTPError as e:
        return {"status": "down", "http": e.code}
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
    ollama = _service_ollama()

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
            "ollama": ollama,
        },
    }
    return payload
