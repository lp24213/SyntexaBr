from fastapi import APIRouter, FastAPI

# Rotas LEVES — importadas no topo (sem IA pesada)
from vereda_backend.api.v1.endpoints import (
    auth,
    calendly,
    desktop_downloads,
    documents,
    education,
    export_api,
    feedback,
    health,
    institutional,
    integrations,
    payments,
    subscription,
    webhooks,
    webhooks_billing,
    whatsapp_integration,
    tiktok_integration,
)
from vereda_backend.api import public
from vereda_backend.core.config import settings

# Rotas que podem carregar IA no import — lazy dentro de register()
_files_api = None
_admin = None
_intel = None


def _load_heavy_modules():
    """Lazy load de módulos pesados."""
    global _files_api, _admin, _intel
    if _files_api is None:
        from vereda_backend.api.v1.endpoints import files_api as _files_api_mod
        _files_api = _files_api_mod
    if _admin is None:
        from vereda_backend.api.v1.endpoints import admin as _admin_mod
        _admin = _admin_mod
    if _intel is None:
        from vereda_backend.api.v1.endpoints import intel as _intel_mod
        _intel = _intel_mod


def register(app: FastAPI) -> None:
    root_router = APIRouter()

    # Health (sempre leve)
    root_router.include_router(health.router, tags=["health"])

    # Chat público na raiz: /public-chat e /public-chat/stream
    root_router.include_router(public.router_root, tags=["public"])

    # Rotas públicas sob /api
    root_router.include_router(public.router, tags=["public"])

    # Versão 1 da API — leve
    api_v1_router = APIRouter(prefix=settings.api_v1_prefix)
    api_v1_router.include_router(public.router_v1, tags=["public"])
    api_v1_router.include_router(auth.router, tags=["auth"])
    api_v1_router.include_router(calendly.router, tags=["calendly"])
    api_v1_router.include_router(whatsapp_integration.router, tags=["whatsapp"])
    api_v1_router.include_router(tiktok_integration.router, tags=["tiktok"])
    api_v1_router.include_router(desktop_downloads.router, tags=["desktop"])
    api_v1_router.include_router(payments.router, tags=["payments"])
    api_v1_router.include_router(subscription.router, tags=["subscription"])
    api_v1_router.include_router(feedback.router, tags=["feedback"])
    api_v1_router.include_router(webhooks.router, tags=["webhooks"])
    api_v1_router.include_router(webhooks_billing.router, tags=["webhooks"])
    api_v1_router.include_router(education.router, tags=["education"])
    api_v1_router.include_router(institutional.router, tags=["institutional"])
    api_v1_router.include_router(integrations.router, tags=["integrations"])
    api_v1_router.include_router(documents.router, tags=["documents"])
    api_v1_router.include_router(export_api.router, tags=["export"])

    # ── Rotas pesadas (IA) — só em modo NÃO-gateway ──
    is_gateway = bool(getattr(settings, "gateway_mode", False))
    if not is_gateway:
        _load_heavy_modules()

        from vereda_backend.api import syntexa_model_api
        api_v1_router.include_router(syntexa_model_api.router, tags=["syntexa-model"])

        from vereda_backend.api.v1.endpoints import (
            admin as _admin_router,
            agents,
            autonomy,
            chat,
            document,
            execution,
            files_api,
            intel as _intel_router,
            media,
            modular_chat,
            multimodal_api,
            research,
            science,
            tools,
            vision,
            voice,
        )

        api_v1_router.include_router(autonomy.router, tags=["autonomy"])
        api_v1_router.include_router(modular_chat.router, tags=["modular-chat"])
        api_v1_router.include_router(chat.router, tags=["chat"])
        api_v1_router.include_router(_admin_router.router, tags=["admin"])
        api_v1_router.include_router(tools.router, tags=["tools"])
        api_v1_router.include_router(media.router, tags=["media"])
        api_v1_router.include_router(multimodal_api.router, tags=["multimodal"])
        api_v1_router.include_router(science.router, tags=["science"])
        api_v1_router.include_router(research.router, tags=["research"])
        api_v1_router.include_router(agents.router, tags=["agents"])
        api_v1_router.include_router(execution.router, tags=["execution"])
        api_v1_router.include_router(vision.router, tags=["vision"])
        api_v1_router.include_router(voice.router, tags=["voice"])
        api_v1_router.include_router(document.router, tags=["document"])
        api_v1_router.include_router(_intel_router.router, tags=["intel"])
        app.include_router(files_api.router, prefix="/api/files", tags=["files"])
    else:
        # Gateway mode: rotas pesadas são proxies ou não expostas
        from vereda_backend.api.v1.endpoints import (
            admin as _admin_router,
            intel as _intel_router,
        )
        api_v1_router.include_router(_admin_router.router, tags=["admin"])
        api_v1_router.include_router(_intel_router.router, tags=["intel"])

    app.include_router(root_router)
    app.include_router(api_v1_router)


def include_api_routes(app: FastAPI) -> None:
    """
    Compat: alias usado por versões anteriores de main.py.
    """
    register(app)
