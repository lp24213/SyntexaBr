from fastapi import APIRouter, FastAPI

from vereda_backend.api.v1.endpoints import (
    admin,
    agents,
    autonomy,
    auth,
    chat,
    desktop_downloads,
    files_api,
    education,
    execution,
    feedback,
    health,
    intel,
    institutional,
    integrations,
    media,
    multimodal_api,
    modular_chat,
    payments,
    research,
    science,
    tools,
    vision,
    webhooks,
)
from vereda_backend.api import public
from vereda_backend.core.config import settings


def register(app: FastAPI) -> None:
    root_router = APIRouter()

    # Health
    root_router.include_router(health.router, tags=["health"])

    # Chat público na raiz: /public-chat e /public-chat/stream
    root_router.include_router(public.router_root, tags=["public"])

    # Rotas públicas sob /api
    root_router.include_router(public.router, tags=["public"])

    # Versão 1 da API, estilo OpenAI + ferramentas + admin + multimídia + ciência + agentes
    api_v1_router = APIRouter(prefix=settings.api_v1_prefix)
    api_v1_router.include_router(public.router_v1, tags=["public"])
    api_v1_router.include_router(auth.router, tags=["auth"])
    api_v1_router.include_router(desktop_downloads.router, tags=["desktop"])
    api_v1_router.include_router(autonomy.router, tags=["autonomy"])
    api_v1_router.include_router(modular_chat.router, tags=["modular-chat"])
    api_v1_router.include_router(chat.router, tags=["chat"])
    api_v1_router.include_router(payments.router, tags=["payments"])
    api_v1_router.include_router(admin.router, tags=["admin"])
    api_v1_router.include_router(tools.router, tags=["tools"])
    api_v1_router.include_router(media.router, tags=["media"])
    api_v1_router.include_router(multimodal_api.router, tags=["multimodal"])
    api_v1_router.include_router(science.router, tags=["science"])
    api_v1_router.include_router(research.router, tags=["research"])
    api_v1_router.include_router(agents.router, tags=["agents"])
    api_v1_router.include_router(execution.router, tags=["execution"])
    api_v1_router.include_router(vision.router, tags=["vision"])
    api_v1_router.include_router(feedback.router, tags=["feedback"])
    api_v1_router.include_router(webhooks.router, tags=["webhooks"])
    api_v1_router.include_router(education.router, tags=["education"])
    api_v1_router.include_router(institutional.router, tags=["institutional"])
    api_v1_router.include_router(integrations.router, tags=["integrations"])
    api_v1_router.include_router(intel.router, tags=["intel"])

    app.include_router(root_router)
    app.include_router(api_v1_router)
    # Rotas estáveis /api/files/* (geração ODS e download) — usadas pelo chat e integrações
    app.include_router(files_api.router, prefix="/api/files", tags=["files"])


def include_api_routes(app: FastAPI) -> None:
    """
    Compat: alias usado por versões anteriores de main.py.
    """
    register(app)
