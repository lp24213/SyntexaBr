from fastapi import FastAPI, APIRouter

from local_private_ai.api.v1.endpoints import health, chat, embeddings


def register_routes(app: FastAPI) -> None:
    root = APIRouter()
    root.include_router(health.router, tags=["health"])

    v1 = APIRouter(prefix="/v1")
    v1.include_router(chat.router, tags=["chat"])
    v1.include_router(embeddings.router, tags=["embeddings"])

    app.include_router(root)
    app.include_router(v1)
