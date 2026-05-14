from fastapi import FastAPI, APIRouter

from worker.api.v1.endpoints import health, chat, embeddings, ocr, tts, stt


def register_routes(app: FastAPI) -> None:
    root = APIRouter()
    root.include_router(health.router, tags=["health"])

    v1 = APIRouter(prefix="/v1")
    v1.include_router(chat.router, tags=["chat"])
    v1.include_router(embeddings.router, tags=["embeddings"])
    v1.include_router(ocr.router, tags=["ocr"])
    v1.include_router(tts.router, tags=["tts"])
    v1.include_router(stt.router, tags=["stt"])

    app.include_router(root)
    app.include_router(v1)
