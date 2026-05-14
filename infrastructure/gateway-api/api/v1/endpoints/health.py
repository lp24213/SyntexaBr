"""Healthcheck para Railway — NÃO acessa DB, Redis, Stripe, IA, Kaggle, APIs externas."""
from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

_START_MONOTONIC = time.monotonic()


def _uptime_seconds() -> float:
    return round(time.monotonic() - _START_MONOTONIC, 2)


@router.get("/health")
def health_check() -> JSONResponse:
    """Responde em <1ms. Zero dependências externas."""
    return JSONResponse(
        content={
            "status": "ok",
            "service": "syntexa-gateway",
            "version": "2.0.0",
            "uptime_seconds": _uptime_seconds(),
            "timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        },
        status_code=200,
    )
