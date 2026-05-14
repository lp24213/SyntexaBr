"""Syntexa Local Private AI — Ollama, modelos privados, inferência offline."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from local_private_ai.core.config import settings
from local_private_ai.api.routes import register_routes

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Local Private AI starting")
    yield
    logger.info("Local Private AI shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Syntexa Local Private AI",
        version="1.0.0",
        description="Ollama integration and private model inference",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(_request: Request, _exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": "Invalid request"})

    @app.exception_handler(HTTPException)
    async def _http_error_handler(_request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def _unhandled_error_handler(_request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Local AI error")
        return JSONResponse(status_code=500, content={"detail": "Internal error"})

    @app.get("/health")
    def health_check() -> dict[str, Any]:
        return {"status": "ok", "service": "syntexa-local-private-ai"}

    register_routes(app)
    return app


app = create_app()
