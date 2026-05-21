#!/usr/bin/env python3
"""Servidor local FastAPI com modelo Syntexa 30M treinado."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from vereda_ai.syntexa_core.foundation_model import SyntexaFoundationModel, SyntexaFoundationConfig
from vereda_ai.syntexa_core.foundation_tokenizer import SyntexaFoundationTokenizer

app = FastAPI(title="Syntexa Local Model Server", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Carrega modelo
CKPT = _ROOT / "checkpoints" / "syntexa_local" / "final"
_device = torch.device("cpu")
_model = None
_tokenizer = None
_cfg = None

print("[LOAD] Carregando modelo Syntexa 30M...")
cfg_dict = json.loads((CKPT / "config.json").read_text())
_cfg = SyntexaFoundationConfig(**cfg_dict)
_model = SyntexaFoundationModel(_cfg)
_model.load_state_dict(torch.load(CKPT / "model.pt", map_location=_device))
_model.to(_device)
_model.eval()
_tokenizer = SyntexaFoundationTokenizer.load(CKPT / "tokenizer")
_params = sum(p.numel() for p in _model.parameters())
print(f"[OK] Modelo carregado: {_params:,} params")


class ChatReq(BaseModel):
    message: str
    max_tokens: int = 64
    temperature: float = 0.8


class ChatResp(BaseModel):
    response: str
    model: str
    tokens_generated: int


@app.get("/health")
def health():
    return {"status": "ok", "model": "syntexa_30m", "params": _params}


@app.post("/v1/chat", response_model=ChatResp)
def chat(req: ChatReq):
    try:
        input_ids = torch.tensor([_tokenizer.encode(req.message)], dtype=torch.long, device=_device)
        with torch.no_grad():
            output = _model.generate(
                input_ids,
                max_new_tokens=req.max_tokens,
                temperature=req.temperature,
                top_k=50,
                top_p=0.9,
            )
        text = _tokenizer.decode(output[0].tolist(), skip_special_tokens=True)
        tokens = output.shape[1] - input_ids.shape[1]
        return ChatResp(response=text, model="syntexa_30m", tokens_generated=tokens)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/status")
def status():
    return {"model_loaded": True, "model_name": "syntexa_30m", "params": _params, "device": str(_device)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
