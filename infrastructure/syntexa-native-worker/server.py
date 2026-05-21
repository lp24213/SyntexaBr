"""Syntexa Native Worker — serve EXCLUSIVAMENTE o motor proprietário syntexa_native.

Sem Ollama. Sem Llama. Sem HuggingFace. Apenas o checkpoint da Foundation Model
do projeto (vereda_ai/syntexa_core).

Endpoint principal: POST /v1/chat/completions  (compatível com o cliente
ai_proxy_client do backend Railway).
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

# Garante que o repositório raiz esteja no PYTHONPATH (para vereda_ai.*)
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from vereda_ai.syntexa_core.foundation_inference import SyntexaInferenceEngine  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
log = logging.getLogger("syntexa.worker")

CHECKPOINT_PATH = os.environ.get(
    "SYNTEXA_CHECKPOINT_PATH",
    str(ROOT / "checkpoints" / "foundation" / "checkpoint_sft_ep20.pt"),
)
TOKENIZER_DIR = os.environ.get(
    "SYNTEXA_TOKENIZER_DIR",
    str(ROOT / "checkpoints" / "foundation" / "tokenizer"),
)
MANIFEST_PATH = os.environ.get(
    "SYNTEXA_MANIFEST_PATH",
    str(ROOT / "checkpoints" / "foundation" / "manifest.json"),
)
EXPECTED_TOKEN = os.environ.get("SYNTEXA_WORKER_TOKEN")

app = FastAPI(title="Syntexa Native Worker", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_engine: Optional[SyntexaInferenceEngine] = None
_load_error: Optional[str] = None


def _build_config_from_manifest() -> Optional[Dict[str, Any]]:
    """Lê manifest.json e converte em SyntexaFoundationConfig kwargs."""
    p = Path(MANIFEST_PATH)
    if not p.is_file():
        return None
    raw = json.loads(p.read_text(encoding="utf-8"))
    return {
        "vocab_size": int(raw.get("vocab_size", 532)),
        "dim": int(raw.get("dim", 128)),
        "num_layers": int(raw.get("num_layers", 2)),
        "num_heads": int(raw.get("num_heads", 2)),
        "num_kv_heads": int(raw.get("num_kv_heads", raw.get("num_heads", 2))),
        "max_seq_len": int(raw.get("max_seq_len", 256)),
    }


def _load_engine() -> None:
    """Carrega o motor proprietário com o checkpoint local. Idempotente."""
    global _engine, _load_error
    if _engine is not None and _engine.is_ready():
        return
    try:
        from vereda_ai.syntexa_core.foundation_model import SyntexaFoundationConfig

        cfg_kwargs = _build_config_from_manifest()
        cfg = SyntexaFoundationConfig(**cfg_kwargs) if cfg_kwargs else None

        engine = SyntexaInferenceEngine()
        engine.load_from_checkpoint(
            checkpoint_path=CHECKPOINT_PATH,
            tokenizer_dir=TOKENIZER_DIR,
            config=cfg,
        )
        _engine = engine
        _load_error = None
        log.info("[boot] Engine syntexa_native pronto. checkpoint=%s", CHECKPOINT_PATH)
    except Exception as exc:
        _load_error = f"{type(exc).__name__}: {exc}"
        log.exception("[boot] Falha ao carregar engine: %s", exc)


@app.on_event("startup")
def _startup() -> None:
    _load_engine()


# ── Schemas (compatíveis com OpenAI / ai_proxy_client) ────────

class ChatMessageIn(BaseModel):
    role: str
    content: str


class ChatRequestIn(BaseModel):
    messages: List[ChatMessageIn] = Field(..., min_length=1)
    model: Optional[str] = "syntexa_native"
    stream: bool = False
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 50
    max_tokens: int = 512


def _check_auth(request: Request) -> None:
    if not EXPECTED_TOKEN:
        return
    auth = request.headers.get("authorization") or ""
    token = auth.removeprefix("Bearer ").strip()
    if token != EXPECTED_TOKEN:
        raise HTTPException(status_code=401, detail="invalid token")


@app.get("/health")
def health() -> Dict[str, Any]:
    if _engine is None:
        _load_engine()
    ready = bool(_engine and _engine.is_ready())
    return {
        "status": "ok" if ready else "degraded",
        "engine": "syntexa_native",
        "ready": ready,
        "checkpoint_path": CHECKPOINT_PATH,
        "tokenizer_dir": TOKENIZER_DIR,
        "load_error": _load_error,
    }


@app.post("/v1/chat/completions")
def chat_completions(req: ChatRequestIn, request: Request) -> Any:
    _check_auth(request)
    if _engine is None or not _engine.is_ready():
        _load_engine()
    if _engine is None or not _engine.is_ready():
        raise HTTPException(status_code=503, detail=f"engine not ready: {_load_error}")

    messages = [m.model_dump() for m in req.messages]

    if req.stream:
        def _gen() -> Iterator[bytes]:
            created = int(time.time())
            for token in _engine.chat_stream(  # type: ignore[union-attr]
                messages,
                max_new_tokens=min(req.max_tokens, 1024),
                temperature=req.temperature,
                top_k=req.top_k,
                top_p=req.top_p,
            ):
                payload = {
                    "id": "chatcmpl-syntexa",
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": "syntexa_native",
                    "choices": [{"index": 0, "delta": {"content": token}, "finish_reason": None}],
                }
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n".encode("utf-8")
            yield b"data: [DONE]\n\n"

        return StreamingResponse(_gen(), media_type="text/event-stream")

    text = _engine.chat(  # type: ignore[union-attr]
        messages,
        max_new_tokens=min(req.max_tokens, 1024),
        temperature=req.temperature,
        top_k=req.top_k,
        top_p=req.top_p,
    )
    return {
        "id": "chatcmpl-syntexa",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": "syntexa_native",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text or ""},
                "finish_reason": "stop",
            }
        ],
        "content": text or "",
    }


@app.get("/v1/stats")
def stats() -> Dict[str, Any]:
    if _engine is None or not _engine.is_ready():
        return {"ready": False}
    return {"ready": True, **_engine.get_stats()}


@app.exception_handler(Exception)
def _global(_req: Request, exc: Exception) -> JSONResponse:
    log.exception("unhandled: %s", exc)
    return JSONResponse(status_code=500, content={"detail": str(exc)})
