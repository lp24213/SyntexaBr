from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from sqlalchemy import inspect, text

from vereda_backend.core.config import settings
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
            }
            for col, sql in pending.items():
                if col not in existing_cols:
                    try:
                        conn.execute(text(sql))
                        log.info("Migração: coluna '%s' adicionada à tabela users.", col)
                    except Exception as e:
                        log.warning("Migração users.%s ignorada: %s", col, e)

        conn.commit()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.project_name,
        version="0.1.0",
        description="Backend da plataforma de IA Syntexa.",
    )

    origins = settings.frontend_origins or ["*"]
    allow_any_origin = "*" in origins
    allow_credentials = not allow_any_origin

    is_production = (settings.environment or "").strip().lower() in {"prod", "production"}

    @app.middleware("http")
    async def security_headers_middleware(request, call_next):
        response = await call_next(request)

        # Core security headers
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=(), payment=()"
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
            "connect-src 'self' https://syntexabr.com.br wss://syntexabr.com.br; "
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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=allow_credentials,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Requested-With", "Accept"],
    )

    api_routes.register(app)

    @app.get("/", response_class=HTMLResponse)
    def serve_index() -> str:
        """
        Serve o frontend estático principal diretamente do backend.
        Assim, o domínio apontando para o gateway/Worker exibe a UI
        mesmo sem depender de Cloudflare Pages.
        """
        index_path = Path(__file__).parent / "static" / "index.html"
        return index_path.read_text(encoding="utf-8")

    @app.on_event("startup")
    def on_startup() -> None:
        # 1. Migra colunas faltantes em tabelas existentes (SQLite não tem ALTER COLUMN)
        _migrate_db()
        # 2. Cria tabelas novas (institutional_clients, etc.)
        Base.metadata.create_all(bind=engine)

        from vereda_backend.db.session import SessionLocal

        db = SessionLocal()
        try:
            # Garante que o admin configurado no .env existe e está atualizado.
            # Se o e-mail mudou, cria um novo. Se já existe, sincroniza senha e flags.
            admin = (
                db.query(models.User)
                .filter(models.User.email == settings.admin_email)
                .first()
            )
            if not admin:
                # Desativa qualquer outro admin existente para evitar duplicatas
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
                # Atualiza senha e garante flags corretas
                admin.hashed_password = get_password_hash(settings.admin_password)
                admin.is_active = True
                admin.is_admin = True
                db.commit()
        finally:
            db.close()

    return app


app = create_app()

