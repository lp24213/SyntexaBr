"""Syntexa AI Worker — Kaggle / GPU / Servidor externo (IA pesada, lazy loading)."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.gzip import GZipMiddleware

from worker.core.config import settings
from worker.api.routes import register_routes

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: NÃO carrega modelos. Lazy loading em primeira requisição."""
    logger.info("AI Worker starting — models will be lazy-loaded on first request")
    yield
    logger.info("AI Worker shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Syntexa AI Worker",
        version="2.0.0",
        description="AI Worker for embeddings, LLM inference, OCR, TTS, STT",
        lifespan=lifespan,
    )

    origins = getattr(settings, "cors_origins", ["*"])
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(_request: Request, _exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": "Invalid request"})

    @app.exception_handler(HTTPException)
    async def _http_error_handler(_request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def _unhandled_error_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("AI Worker error")
        return JSONResponse(status_code=500, content={"detail": "Internal error"})

    # ── Healthcheck instantâneo — não carrega modelos ──
    @app.get("/health")
    def health_check() -> dict[str, Any]:
        return {"status": "ok", "service": "syntexa-ai-worker", "version": "2.0.0"}

    register_routes(app)
    return app


app = create_app()
