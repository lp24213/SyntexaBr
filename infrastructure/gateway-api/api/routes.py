from fastapi import FastAPI, APIRouter

from gateway.api.v1.endpoints import health, proxy_chat, proxy_embeddings, proxy_media


def register_routes(app: FastAPI) -> None:
    root = APIRouter()
    root.include_router(health.router, tags=["health"])

    v1 = APIRouter(prefix="/v1")
    v1.include_router(proxy_chat.router, tags=["proxy-chat"])
    v1.include_router(proxy_embeddings.router, tags=["proxy-embeddings"])
    v1.include_router(proxy_media.router, tags=["proxy-media"])

    app.include_router(root)
    app.include_router(v1)
