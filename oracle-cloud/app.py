"""Syntexa Backend + AI Worker - Oracle Cloud Edition

Roda em CPU (Oracle Always Free) ou GPU (com créditos trial).
Lazy loading dos modelos de IA.
"""
from __future__ import annotations

import logging
import os
import threading
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Config
PORT = int(os.environ.get("PORT", 8000))
MODEL_PATH = os.environ.get("LOCAL_LLM_MODEL", "microsoft/DialoGPT-medium")
EMBED_MODEL = os.environ.get("LOCAL_EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
DEVICE = os.environ.get("AI_DEVICE", "auto")  # auto, cpu, cuda

# Locks para lazy loading
_llm_lock = threading.Lock()
_embed_lock = threading.Lock()

_llm_pipe: Any = None
_embed_model: Any = None


def _detect_device() -> str:
    if DEVICE != "auto":
        return DEVICE
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def _load_llm() -> Any:
    global _llm_pipe
    if _llm_pipe is not None:
        return _llm_pipe
    with _llm_lock:
        if _llm_pipe is not None:
            return _llm_pipe
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

            device = _detect_device()
            logger.info("Loading LLM %s on %s...", MODEL_PATH, device)

            tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH)
            if device == "cuda":
                model = AutoModelForCausalLM.from_pretrained(
                    MODEL_PATH,
                    torch_dtype=torch.float16,
                    device_map="auto",
                )
                _llm_pipe = pipeline(
                    "text-generation",
                    model=model,
                    tokenizer=tokenizer,
                    torch_dtype=torch.float16,
                    device=0,
                )
            else:
                model = AutoModelForCausalLM.from_pretrained(
                    MODEL_PATH,
                    torch_dtype=torch.float32,
                    device_map="cpu",
                    low_cpu_mem_usage=True,
                )
                _llm_pipe = pipeline(
                    "text-generation",
                    model=model,
                    tokenizer=tokenizer,
                    torch_dtype=torch.float32,
                    device=-1,
                )
            logger.info("LLM loaded on %s", device)
        except Exception as exc:
            logger.error("LLM load failed: %s", exc)
            raise
    return _llm_pipe


def _load_embed() -> Any:
    global _embed_model
    if _embed_model is not None:
        return _embed_model
    with _embed_lock:
        if _embed_model is not None:
            return _embed_model
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("Loading embeddings %s...", EMBED_MODEL)
            _embed_model = SentenceTransformer(EMBED_MODEL)
            logger.info("Embeddings loaded")
        except Exception as exc:
            logger.error("Embeddings failed: %s", exc)
            raise
    return _embed_model


def generate_chat(messages: list[dict[str, str]], *, temperature: float = 0.7, max_tokens: int = 512) -> str:
    pipe = _load_llm()
    prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
    result = pipe(
        prompt,
        max_new_tokens=max_tokens,
        temperature=temperature,
        do_sample=True,
        return_full_text=False,
        pad_token_id=pipe.tokenizer.eos_token_id,
    )
    return result[0]["generated_text"].strip()


def embed_texts(texts: list[str]) -> list[list[float]]:
    model = _load_embed()
    vectors = model.encode(texts, convert_to_numpy=True)
    return [vec.tolist() for vec in vectors]


# === FASTAPI APP ===
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Syntexa Oracle Cloud starting...")
    yield
    logger.info("Syntexa Oracle Cloud stopping...")

app = FastAPI(
    title="Syntexa AI - Oracle Cloud",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "syntexa-ai-oracle", "device": _detect_device()}


class ChatRequest(BaseModel):
    messages: list[dict[str, str]]
    model: str | None = "default"
    temperature: float = 0.7
    max_tokens: int = 512


@app.post("/v1/chat/completions")
def chat(req: ChatRequest):
    try:
        text = generate_chat(req.messages, temperature=req.temperature, max_tokens=req.max_tokens)
        return {
            "choices": [{"message": {"role": "assistant", "content": text}, "finish_reason": "stop", "index": 0}],
            "model": req.model or "default",
        }
    except Exception as exc:
        logger.error("Chat error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Generation failed: {exc}")


class EmbedRequest(BaseModel):
    texts: list[str]
    model: str | None = "default"


@app.post("/v1/embeddings")
def embed(req: EmbedRequest):
    try:
        vectors = embed_texts(req.texts)
        return {
            "data": [{"index": i, "embedding": vec, "object": "embedding"} for i, vec in enumerate(vectors)],
            "model": req.model or "default",
        }
    except Exception as exc:
        logger.error("Embed error: %s", exc)
        raise HTTPException(status_code=500, detail=f"Embedding failed: {exc}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
