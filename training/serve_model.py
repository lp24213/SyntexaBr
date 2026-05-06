#!/usr/bin/env python3
"""
Servidor HTTP de inferência para checkpoint proprietário (FastAPI).
Expõe endpoint OpenAI-like:
- POST /v1/chat/completions
- GET  /health
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any
import sys

from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import uvicorn

try:
    import torch
except Exception:  # pragma: no cover
    torch = None

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from training.model_syntexa import SyntexaConfig, SyntexaDecoderLM
from vereda_ai.syntexa_core.model_manifest import ModelManifest
from vereda_ai.syntexa_core.tokenizer import SyntexaTokenizer


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str = "syntexa-small"
    messages: list[ChatMessage]
    max_tokens: int = 256
    temperature: float = 0.9


def _sse_stream_text(text: str, chunk: int = 96):
    import json as _json

    for i in range(0, len(text), chunk):
        part = text[i : i + chunk]
        yield f"data: {_json.dumps({'content': part}, ensure_ascii=False)}\n\n"


def _build_prompt(messages: list[ChatMessage]) -> str:
    parts: list[str] = []
    for m in messages:
        role = (m.role or "user").upper()
        parts.append(f"{role}: {m.content}")
    parts.append("ASSISTANT:")
    return "\n".join(parts)


def _load_runtime(manifest_or_dir: Path, device: str) -> tuple[SyntexaDecoderLM, SyntexaTokenizer, str]:
    if manifest_or_dir.is_dir():
        mf = manifest_or_dir / "manifest.json"
    else:
        mf = manifest_or_dir
    manifest = ModelManifest.from_file(mf)
    tok = SyntexaTokenizer.load(manifest.tokenizer_path)
    payload = torch.load(manifest.checkpoint_path, map_location=device)
    cfg = SyntexaConfig(**payload.get("config", {}))
    model = SyntexaDecoderLM(cfg).to(device)
    model.load_state_dict(payload["model_state"], strict=True)
    model.eval()
    return model, tok, manifest.name


def main() -> None:
    ap = argparse.ArgumentParser(description="Servir modelo Syntexa (inferência própria)")
    ap.add_argument("--checkpoint", required=True, help="Manifest.json ou diretório do checkpoint")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=9000)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()
    if torch is None:
        raise SystemExit("Torch não encontrado. Instale torch para servir o modelo.")

    device = args.device
    if device.startswith("cuda") and not torch.cuda.is_available():
        device = "cpu"

    model, tok, loaded_name = _load_runtime(Path(args.checkpoint), device)
    app = FastAPI(title="Syntexa Own Model Server")

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {"ok": True, "model": loaded_name, "device": device}

    @app.post("/v1/chat/completions")
    def chat(req: ChatRequest) -> dict[str, Any]:
        prompt = _build_prompt(req.messages)
        ids = tok.encode(prompt, add_special_tokens=True, max_length=model.cfg.max_seq_len)
        out_ids = model.generate(
            ids,
            max_new_tokens=max(1, min(2048, int(req.max_tokens))),
            temperature=float(req.temperature),
            eos_id=tok.eos_id,
            device=device,
        )
        text = tok.decode(out_ids[len(ids) :]).strip()
        if not text:
            text = "Model generated an empty completion."
        return {
            "id": "chatcmpl-syntexa-own",
            "object": "chat.completion",
            "model": req.model or loaded_name,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": len(ids), "completion_tokens": max(1, len(out_ids) - len(ids)), "total_tokens": len(out_ids)},
        }

    @app.post("/v1/chat/completions/stream")
    def chat_stream(req: ChatRequest):
        payload = chat(req)
        text = str(payload["choices"][0]["message"]["content"])
        return StreamingResponse(
            _sse_stream_text(text),
            media_type="text/event-stream; charset=utf-8",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
