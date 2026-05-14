"""
VEREDA / SYNTEXA — AWS GPU Cluster Server
=========================================
Servidor unificado para vLLM, embeddings, vision e voice.
Baseado em FastAPI com lazy loading de modelos.
"""

import os
import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse

log = logging.getLogger(__name__)

# ── LAZY LOADER REGISTRY ───────────────────────────────────
_MODEL_REGISTRY = {}


def _lazy_load(name: str, factory):
    """Carrega modelo apenas na primeira requisição."""
    if name not in _MODEL_REGISTRY:
        log.info("Lazy loading model: %s", name)
        _MODEL_REGISTRY[name] = factory()
    return _MODEL_REGISTRY[name]


# ── SERVICE MODE ────────────────────────────────────────────
SERVICE_MODE = os.getenv("SERVICE_MODE", "llm")  # llm | embeddings | vision | voice


# ── LIFESPAN (startup/shutdown) ─────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("AWS GPU Cluster starting — mode: %s", SERVICE_MODE)
    yield
    log.info("AWS GPU Cluster shutting down")
    for name, model in _MODEL_REGISTRY.items():
        log.info("Unloading model: %s", name)


# ── APP FACTORY ─────────────────────────────────────────────
def create_app() -> FastAPI:
    app = FastAPI(
        title="Vereda GPU Cluster",
        version="3.0.0",
        lifespan=lifespan,
    )

    @app.get("/health")
    def health():
        return {"status": "ok", "mode": SERVICE_MODE, "gpu": True}

    @app.get("/health/detailed")
    def health_detailed():
        import torch
        return {
            "status": "ok",
            "mode": SERVICE_MODE,
            "cuda_available": torch.cuda.is_available(),
            "cuda_devices": torch.cuda.device_count(),
            "loaded_models": list(_MODEL_REGISTRY.keys()),
        }

    # ── LLM ENDPOINTS ──────────────────────────────────────
    if SERVICE_MODE in ("llm", "all"):
        @app.post("/v1/chat/completions")
        async def chat_completions(request: dict):
            # Proxy para vLLM interno ou carrega modelo
            # Em produção, usar vLLM server standalone na porta 8000
            return {"status": "ok", "message": "vLLM proxy — use vllm service diretamente na porta 8000"}

        @app.get("/v1/models")
        def list_models():
            return {"object": "list", "data": []}

    # ── EMBEDDINGS ENDPOINTS ────────────────────────────────
    if SERVICE_MODE in ("embeddings", "all"):
        @app.post("/v1/embeddings")
        async def create_embeddings(request: dict):
            model_name = request.get("model", "default")
            inputs = request.get("input", [])

            def _load_embedder():
                from sentence_transformers import SentenceTransformer
                m = os.getenv("EMBEDDING_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
                return SentenceTransformer(m, device="cuda")

            embedder = _lazy_load(f"embedder:{model_name}", _load_embedder)
            vectors = embedder.encode(inputs, convert_to_numpy=True).tolist()
            return {
                "object": "list",
                "data": [{"object": "embedding", "embedding": v, "index": i} for i, v in enumerate(vectors)],
                "model": model_name,
            }

    # ── VISION ENDPOINTS ────────────────────────────────────
    if SERVICE_MODE in ("vision", "all"):
        @app.post("/v1/vision/describe")
        async def vision_describe(request: dict):
            return {"description": "Vision endpoint — implementar com modelo multimodal"}

        @app.post("/v1/vision/ocr")
        async def vision_ocr(request: dict):
            return {"text": "OCR endpoint — implementar com pytesseract / easyocr"}

    # ── VOICE ENDPOINTS ─────────────────────────────────────
    if SERVICE_MODE in ("voice", "all"):
        @app.post("/v1/voice/stt")
        async def voice_stt(request: dict):
            return {"text": "STT endpoint — implementar com Whisper"}

        @app.post("/v1/voice/tts")
        async def voice_tts(request: dict):
            return {"audio_url": "TTS endpoint — implementar com Piper/Coqui"}

    return app


# ── MULTI-APP EXPORT (para uvicorn modular) ──────────────────
app = create_app()

embeddings_app = create_app()
vision_app = create_app()
voice_app = create_app()

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, workers=1)
