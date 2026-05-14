"""Syntexa Gateway API — Railway (leve, sem IA pesada)."""
from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request, WebSocket
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.gzip import GZipMiddleware

from gateway.core.config import settings
from gateway.core.public_messages import MSG_BAD_REQUEST_PT, MSG_TRY_AGAIN_PT
from gateway.api.routes import register_routes

logger = logging.getLogger(__name__)

# ── Startup timing guarantee ──────────────────────────────────────────
_START_MONOTONIC = time.monotonic()


def _uptime_seconds() -> float:
    return round(time.monotonic() - _START_MONOTONIC, 2)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup leve: NÃO carrega IA, modelos, embeddings, etc."""
    logger.info("Gateway API starting (lightweight mode)")
    yield
    logger.info("Gateway API shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.project_name,
        version="2.0.0",
        description="Syntexa Gateway API — Lightweight Railway Layer",
        lifespan=lifespan,
    )

    origins = settings.frontend_origins or ["*"]
    allow_any_origin = "*" in origins
    allow_credentials = not allow_any_origin
    is_production = (settings.environment or "").strip().lower() in {"prod", "production"}

    @app.middleware("http")
    async def timing_middleware(request: Request, call_next):
        t0 = time.perf_counter()
        response = await call_next(request)
        dt_ms = (time.perf_counter() - t0) * 1000.0
        response.headers["X-Process-Time-Ms"] = f"{dt_ms:.1f}"
        return response

    @app.middleware("http")
    async def cloudflare_origin_guard(request: Request, call_next):
        if getattr(settings, "require_cloudflare", False):
            path = request.url.path
            skip = {"/health", "/docs", "/openapi.json", "/redoc"}
            if path in skip or path.startswith("/static"):
                pass
            elif not request.headers.get("cf-connecting-ip"):
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Acesso direto ao origin não permitido. Use o domínio protegido por Cloudflare."},
                )
        return await call_next(request)

    @app.middleware("http")
    async def security_headers_middleware(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=(), payment=()"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
            "https://cdn.jsdelivr.net https://unpkg.com https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' "
            "https://cdn.jsdelivr.net https://fonts.googleapis.com https://cdnjs.cloudflare.com; "
            "font-src 'self' data: https://fonts.gstatic.com https://cdn.jsdelivr.net; "
            "img-src 'self' data: blob: https:; "
            "connect-src 'self' https://syntexabr.com.br https://www.syntexabr.com.br https://api.syntexabr.com.br "
            "wss://syntexabr.com.br wss://www.syntexabr.com.br wss://api.syntexabr.com.br; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        response.headers["Content-Security-Policy"] = csp
        if is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )
        origin = request.headers.get("origin")
        if allow_any_origin:
            response.headers.setdefault("Access-Control-Allow-Origin", "*")
        elif origin and origin in origins:
            response.headers.setdefault("Access-Control-Allow-Origin", origin)
        response.headers.setdefault(
            "Access-Control-Allow-Methods",
            "GET, POST, PUT, PATCH, DELETE, OPTIONS",
        )
        response.headers.setdefault(
            "Access-Control-Allow-Headers",
            "Authorization, Content-Type, X-Requested-With, Accept",
        )
        return response

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=allow_credentials,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Requested-With", "Accept"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(_request: Request, _exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": MSG_BAD_REQUEST_PT})

    @app.exception_handler(HTTPException)
    async def _http_error_handler(_request: Request, exc: HTTPException) -> JSONResponse:
        if exc.status_code >= 500:
            logger.warning("HTTP %s (resposta sanitizada)", exc.status_code)
            return JSONResponse(status_code=503, content={"detail": MSG_TRY_AGAIN_PT})
        if exc.status_code == 400:
            return JSONResponse(status_code=400, content={"detail": MSG_BAD_REQUEST_PT})
        if exc.status_code == 401:
            return JSONResponse(
                status_code=401,
                content={"detail": "Sessão expirada ou acesso não autorizado. Entre novamente."},
            )
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def _unhandled_error_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Erro interno não tratado no gateway")
        return JSONResponse(status_code=503, content={"detail": MSG_TRY_AGAIN_PT})

    # ── CRITICAL: Healthcheck INSTANTÂNEO — NÃO toca DB/Redis/Stripe/IA ──
    @app.get("/health")
    def health_check() -> JSONResponse:
        """Responde instantaneamente. Não acessa nenhum serviço externo."""
        return JSONResponse(
            content={
                "status": "ok",
                "service": "syntexa-gateway",
                "version": "2.0.0",
                "uptime_seconds": _uptime_seconds(),
            },
            status_code=200,
        )

    register_routes(app)
    return app


app = create_app()
