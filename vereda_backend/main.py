import logging
import time
from pathlib import Path
import json

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

try:
    from starlette.responses import ORJSONResponse as _ORJSONResponse
except Exception:  # pragma: no cover — requer pacote `orjson`
    _ORJSONResponse = None  # type: ignore[misc, assignment]
from starlette.middleware.gzip import GZipMiddleware
from sqlalchemy import inspect, text

from vereda_backend.core.config import settings
from vereda_backend.core.public_messages import MSG_BAD_REQUEST_PT, MSG_TRY_AGAIN_PT
from vereda_backend.core.security_config import ALLOWED_ORIGINS
from vereda_backend.middleware.rate_limit import rate_limiter
from vereda_backend.api import routes as api_routes
from vereda_backend.db.session import Base, engine
from vereda_backend.db import models
from vereda_backend.core.security import get_password_hash


def _migrate_db() -> None:
    """
    Aplica colunas/tabelas novas em bancos existentes sem destruir dados.
    Compatível com SQLite e PostgreSQL.
    """
    import logging
    log = logging.getLogger(__name__)

    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())

    with engine.connect() as conn:
        # ── Tabela users: colunas adicionadas em versões recentes ───────────
        if "users" in existing_tables:
            existing_cols = {c["name"] for c in inspector.get_columns("users")}
            pending = {
                "role":              "ALTER TABLE users ADD COLUMN role VARCHAR(32) NOT NULL DEFAULT 'user'",
                "subscription_plan": "ALTER TABLE users ADD COLUMN subscription_plan VARCHAR(32) NOT NULL DEFAULT 'free'",
                "document":          "ALTER TABLE users ADD COLUMN document VARCHAR(32)",
                "cep":               "ALTER TABLE users ADD COLUMN cep VARCHAR(16)",
                "state":             "ALTER TABLE users ADD COLUMN state VARCHAR(64)",
                "city":              "ALTER TABLE users ADD COLUMN city VARCHAR(128)",
                "address_line":      "ALTER TABLE users ADD COLUMN address_line VARCHAR(255)",
                "address_number":    "ALTER TABLE users ADD COLUMN address_number VARCHAR(32)",
                "address_complement":"ALTER TABLE users ADD COLUMN address_complement VARCHAR(255)",
                "totp_secret":       "ALTER TABLE users ADD COLUMN totp_secret VARCHAR(64)",
                "totp_enabled":      "ALTER TABLE users ADD COLUMN totp_enabled BOOLEAN NOT NULL DEFAULT 0",
                "backup_codes_json": "ALTER TABLE users ADD COLUMN backup_codes_json TEXT",
                "username":          "ALTER TABLE users ADD COLUMN username VARCHAR(64)",
                "avatar_url":        "ALTER TABLE users ADD COLUMN avatar_url TEXT",
            }
            for col, sql in pending.items():
                if col not in existing_cols:
                    try:
                        conn.execute(text(sql))
                        log.info("Migração: coluna '%s' adicionada à tabela users.", col)
                    except Exception as e:
                        log.warning("Migração users.%s ignorada: %s", col, e)

        if "conversation_logs" in existing_tables:
            existing_cols = {c["name"] for c in inspector.get_columns("conversation_logs")}
            pending = {
                "model_used": "ALTER TABLE conversation_logs ADD COLUMN model_used VARCHAR(64)",
                "prompt_tokens": "ALTER TABLE conversation_logs ADD COLUMN prompt_tokens INTEGER",
                "completion_tokens": "ALTER TABLE conversation_logs ADD COLUMN completion_tokens INTEGER",
                "total_tokens": "ALTER TABLE conversation_logs ADD COLUMN total_tokens INTEGER",
                "latency_ms": "ALTER TABLE conversation_logs ADD COLUMN latency_ms DOUBLE PRECISION",
                "detected_language": "ALTER TABLE conversation_logs ADD COLUMN detected_language VARCHAR(16)",
                "detected_subject": "ALTER TABLE conversation_logs ADD COLUMN detected_subject VARCHAR(128)",
                "detected_sentiment": "ALTER TABLE conversation_logs ADD COLUMN detected_sentiment VARCHAR(32)",
            }
            for col, sql in pending.items():
                if col not in existing_cols:
                    try:
                        conn.execute(text(sql))
                        log.info("Migração: coluna '%s' adicionada à tabela conversation_logs.", col)
                    except Exception as e:
                        log.warning("Migração conversation_logs.%s ignorada: %s", col, e)

        if "memory_items" in existing_tables:
            existing_cols = {c["name"] for c in inspector.get_columns("memory_items")}
            pending = {
                "language": "ALTER TABLE memory_items ADD COLUMN language VARCHAR(16)",
                "subject": "ALTER TABLE memory_items ADD COLUMN subject VARCHAR(128)",
                "sentiment": "ALTER TABLE memory_items ADD COLUMN sentiment VARCHAR(32)",
                "source": "ALTER TABLE memory_items ADD COLUMN source VARCHAR(64) DEFAULT 'chat'",
                "embedding_json": "ALTER TABLE memory_items ADD COLUMN embedding_json TEXT",
                "last_seen_at": "ALTER TABLE memory_items ADD COLUMN last_seen_at TIMESTAMP",
            }
            if "embedding_vector" not in existing_cols:
                if engine.dialect.name == "postgresql":
                    pending["embedding_vector"] = (
                        f"ALTER TABLE memory_items ADD COLUMN embedding_vector "
                        f"vector({models.EMBEDDING_VECTOR_DIM})"
                    )
                else:
                    pending["embedding_vector"] = (
                        "ALTER TABLE memory_items ADD COLUMN embedding_vector BLOB"
                    )
            for col, sql in pending.items():
                if col not in existing_cols:
                    try:
                        conn.execute(text(sql))
                        log.info("Migração: coluna '%s' adicionada à tabela memory_items.", col)
                    except Exception as e:
                        log.warning("Migração memory_items.%s ignorada: %s", col, e)

        if "messages" in existing_tables:
            existing_cols = {c["name"] for c in inspector.get_columns("messages")}
            pending: dict[str, str] = {}
            if "embedding_json" not in existing_cols:
                pending["embedding_json"] = "ALTER TABLE messages ADD COLUMN embedding_json TEXT"
            if "metadata_json" not in existing_cols:
                pending["metadata_json"] = "ALTER TABLE messages ADD COLUMN metadata_json TEXT"
            if "embedding_vector" not in existing_cols:
                if engine.dialect.name == "postgresql":
                    pending["embedding_vector"] = (
                        f"ALTER TABLE messages ADD COLUMN embedding_vector "
                        f"vector({models.EMBEDDING_VECTOR_DIM})"
                    )
                else:
                    pending["embedding_vector"] = (
                        "ALTER TABLE messages ADD COLUMN embedding_vector BLOB"
                    )
            for col, sql in pending.items():
                try:
                    conn.execute(text(sql))
                    log.info("Migração: coluna '%s' adicionada à tabela messages.", col)
                except Exception as e:
                    log.warning("Migração messages.%s ignorada: %s", col, e)

        conn.commit()


def create_app() -> FastAPI:
    # ── CONFIGURE LOGGING: Reduzir verbosidade para Railway ──
    import warnings
    import logging.config
    
    # Desabilitar warnings desnecessários
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    warnings.filterwarnings("ignore", category=ResourceWarning)
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    
    # Reduzir logging de bibliotecas heavy
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("anyio").setLevel(logging.WARNING)
    logging.getLogger("starlette").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("vereda_backend").setLevel(logging.INFO)
    
    # Desabilitar tracemalloc warnings
    logging.captureWarnings(False)
    
    app_kw = dict(
        title=settings.project_name,
        version="0.1.0",
        description="Backend da plataforma de IA Syntexa.",
    )
    if _ORJSONResponse is not None:
        app_kw["default_response_class"] = _ORJSONResponse
    app = FastAPI(**app_kw)

    # ── HEALTHCHECK INSTANTÂNEO: registrado ANTES de tudo ──
    # O Railway faz healthcheck imediatamente; esta rota deve responder
    # mesmo se o banco, Redis, IA ou qualquer outra dependência estiver offline.
    @app.get("/health")
    def health_instant() -> dict:
        return {"status": "ok"}

    # ── CORS Configuration (Cloudflare + Frontend) ──
    origins = ALLOWED_ORIGINS or settings.frontend_origins or ["*"]
    allow_any_origin = "*" in origins
    allow_credentials = not allow_any_origin

    is_production = (settings.environment or "").strip().lower() in {"prod", "production"}

    @app.middleware("http")
    async def timing_middleware(request, call_next):
        t0 = time.perf_counter()
        response = await call_next(request)
        dt_ms = (time.perf_counter() - t0) * 1000.0
        response.headers["X-Process-Time-Ms"] = f"{dt_ms:.1f}"
        # NÃO logar TODAS as requisições — reduzir rate limit
        # Apenas logar erros 5xx
        if response.status_code >= 500:
            try:
                log.error(
                    json.dumps(
                        {
                            "event": "http_error",
                            "method": request.method,
                            "path": request.url.path,
                            "status": response.status_code,
                            "latency_ms": round(dt_ms, 2),
                        },
                        ensure_ascii=False,
                    )
                )
            except Exception:
                pass
        return response

    @app.middleware("http")
    async def cloudflare_origin_guard(request, call_next):
        """Opcional: exige presença de CF-Connecting-IP (tráfego via Cloudflare)."""
        if getattr(settings, "require_cloudflare", False):
            path = request.url.path
            if path in ("/health", "/docs", "/openapi.json", "/redoc") or path.startswith("/static"):
                pass
            elif not (request.headers.get("cf-connecting-ip") or request.headers.get("CF-Connecting-IP")):
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Acesso direto ao origin não permitido. Use o domínio protegido por Cloudflare."},
                )
        return await call_next(request)

    @app.middleware("http")
    async def security_headers_middleware(request, call_next):
        response = await call_next(request)

        # Core security headers
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(self), camera=(self), payment=()"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Content-Security-Policy — previne XSS e injeção de scripts
        # Permite: script/style do CDN KaTeX, fonts do Google, imagens e data URIs
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

        # HSTS — força HTTPS em produção (2 anos + subdomains + preload)
        if is_production:
            response.headers["Strict-Transport-Security"] = (
                "max-age=63072000; includeSubDomains; preload"
            )

        # CORS (cobre respostas de erro que o CORSMiddleware oficial não cobre)
        if allow_any_origin:
            response.headers.setdefault("Access-Control-Allow-Origin", "*")
        else:
            origin = request.headers.get("origin")
            if origin and origin in origins:
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

    # ── Rate Limiting Middleware (Redis-backed, distribuído) ──
    @app.middleware("http")
    async def rate_limit_middleware(request, call_next):
        """Rate limit por IP do cliente (respeitando X-Forwarded-For)"""
        # Whitelist caminhos que NÃO devem ter rate limit
        bypass_paths = {"/health", "/docs", "/openapi.json", "/redoc"}
        if request.url.path in bypass_paths:
            return await call_next(request)
        
        await rate_limiter.middleware(request)
        return await call_next(request)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=allow_credentials,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Requested-With", "Accept"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    log = logging.getLogger(__name__)

    @app.exception_handler(RequestValidationError)
    async def _validation_error_handler(_request: Request, _exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(status_code=422, content={"detail": MSG_BAD_REQUEST_PT})

    @app.exception_handler(HTTPException)
    async def _http_error_handler(_request: Request, exc: HTTPException) -> JSONResponse:
        if exc.status_code >= 500:
            log.warning("HTTP %s (resposta sanitizada)", exc.status_code)
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
        log.exception("Erro interno não tratado")
        return JSONResponse(status_code=503, content={"detail": MSG_TRY_AGAIN_PT})

    api_routes.register(app)

    # ── Frontend agora está em Cloudflare Pages, não precisa servir de aqui ──
    # @app.get("/", response_class=HTMLResponse)
    # def serve_index() -> str:
    #     """Serve o frontend estático principal do backend."""
    #     index_path = Path(__file__).parent / "static" / "index.html"
    #     return index_path.read_text(encoding="utf-8")

    @app.on_event("startup")
    async def on_startup() -> None:
        import asyncio

        # ── Healthcheck já responde antes de qualquer carga pesada ──
        # DB migration, admin seed e IA runtime rodam em background
        # para não bloquear o boot do FastAPI.

        async def _heavy_startup() -> None:
            try:
                _migrate_db()
                Base.metadata.create_all(bind=engine)
            except Exception as exc:
                log.warning("DB migration/create skipped: %s", exc)

            try:
                from vereda_backend.db.session import SessionLocal
                db = SessionLocal()
                try:
                    admin = (
                        db.query(models.User)
                        .filter(models.User.email == settings.admin_email)
                        .first()
                    )
                    if not admin:
                        old_admins = db.query(models.User).filter(models.User.is_admin == True).all()
                        for old in old_admins:
                            old.is_admin = False
                        admin = models.User(
                            email=settings.admin_email,
                            full_name="Administrador Syntexa",
                            hashed_password=get_password_hash(settings.admin_password),
                            is_active=True,
                            is_admin=True,
                            role="user",
                        )
                        db.add(admin)
                        db.commit()
                    else:
                        admin.hashed_password = get_password_hash(settings.admin_password)
                        admin.is_active = True
                        admin.is_admin = True
                        db.commit()
                finally:
                    db.close()
            except Exception as exc:
                log.warning("Admin seed skipped: %s", exc)

            is_gateway_mode = bool(getattr(settings, "gateway_mode", False))
            if not is_gateway_mode:
                try:
                    from vereda_backend.core.runtime_watchdog import start_runtime_watchdog
                    start_runtime_watchdog()
                except Exception as e:
                    log.warning("Runtime watchdog skipped: %s", e)
                try:
                    from vereda_backend.services.autonomy_manager import start_autonomy_manager
                    start_autonomy_manager()
                except Exception as e:
                    log.warning("Autonomy manager skipped: %s", e)
                if bool(getattr(settings, "autonomy_evolution_loop_enabled", False)):
                    try:
                        from vereda_backend.services.autonomous_evolution import start_evolution_loop
                        start_evolution_loop()
                    except Exception as e:
                        log.warning("Evolution loop skipped: %s", e)
                try:
                    from vereda_backend.core.sovereign_integration import init_sovereign_runtime
                    init_sovereign_runtime()
                except Exception as e:
                    log.warning("Sovereign runtime initialization skipped: %s", e)
            else:
                log.info("Gateway mode: IA-heavy services NOT loaded on startup.")

        asyncio.create_task(_heavy_startup())

    return app


app = create_app()

