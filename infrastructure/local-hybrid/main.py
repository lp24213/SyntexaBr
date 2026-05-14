"""
VEREDA / SYNTEXA — Local Hybrid AI Server
==========================================
Proxy leve para Ollama + embeddings locais + fallback sync.
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
import httpx

log = logging.getLogger(__name__)

# ── CONFIG ──────────────────────────────────────────────────
OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")
LOCAL_AI_API_KEY = os.getenv("LOCAL_AI_API_KEY", "")
SERVICE_MODE = os.getenv("SERVICE_MODE", "all")

# ── LIFESPAN ────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("Local Hybrid AI starting — mode: %s", SERVICE_MODE)
    app.state.client = httpx.AsyncClient(timeout=httpx.Timeout(120.0))
    yield
    await app.state.client.aclose()
    log.info("Local Hybrid AI shutting down")


# ── APP ─────────────────────────────────────────────────────
app = FastAPI(
    title="Vereda Local Hybrid AI",
    version="3.0.0",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {"status": "ok", "mode": "local-hybrid", "ollama": OLLAMA_ENDPOINT}


@app.get("/health/detailed")
async def health_detailed():
    ollama_status = "unknown"
    try:
        r = await app.state.client.get(f"{OLLAMA_ENDPOINT}/api/tags", timeout=5.0)
        ollama_status = "ok" if r.status_code == 200 else f"error:{r.status_code}"
    except Exception as e:
        ollama_status = f"unreachable:{e}"

    return {
        "status": "ok",
        "mode": "local-hybrid",
        "ollama_status": ollama_status,
        "service_mode": SERVICE_MODE,
    }


# ── LLM PROXY ─────────────────────────────────────────────
@app.post("/v1/chat/completions")
async def chat_completions(request: dict):
    """Proxy para Ollama com formato OpenAI-compatible."""
    model = request.get("model", "qwen2.5:7b")
    messages = request.get("messages", [])
    stream = request.get("stream", False)

    ollama_body = {
        "model": model,
        "messages": messages,
        "stream": stream,
    }

    if stream:
        async def _stream():
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
                    f"{OLLAMA_ENDPOINT}/api/chat",
                    json=ollama_body,
                ) as resp:
                    async for line in resp.aiter_lines():
                        if line:
                            yield f"data: {line}\n\n"
            yield "data: [DONE]\n\n"

        return StreamingResponse(_stream(), media_type="text/event-stream")

    r = await app.state.client.post(f"{OLLAMA_ENDPOINT}/api/chat", json=ollama_body)
    return r.json()


# ── EMBEDDINGS ──────────────────────────────────────────────
@app.post("/v1/embeddings")
async def create_embeddings(request: dict):
    model = request.get("model", "nomic-embed-text")
    inputs = request.get("input", [])
    if isinstance(inputs, str):
        inputs = [inputs]

    r = await app.state.client.post(
        f"{OLLAMA_ENDPOINT}/api/embed",
        json={"model": model, "input": inputs},
    )
    data = r.json()
    return {
        "object": "list",
        "data": [{"object": "embedding", "embedding": emb, "index": i} for i, emb in enumerate(data.get("embeddings", []))],
        "model": model,
    }


# ── VISION / OCR (placeholder — implementar com modelos locais) ──
@app.post("/v1/vision/describe")
async def vision_describe():
    return {"description": "Vision local — implementar com modelo multimodal local"}


@app.post("/v1/vision/ocr")
async def vision_ocr():
    return {"text": "OCR local — implementar com pytesseract / easyocr"}


# ── VOICE (placeholder) ───────────────────────────────────
@app.post("/v1/voice/stt")
async def voice_stt():
    return {"text": "STT local — implementar com whisper.cpp"}


@app.post("/v1/voice/tts")
async def voice_tts():
    return {"audio_url": "TTS local — implementar com piper"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002, workers=1)
