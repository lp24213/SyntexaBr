"""
SYNTEXA MODEL API - FastAPI endpoint para o modelo 30M treinado
Roda tanto local quanto no Railway (se RAM permitir)
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import torch
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/v1/model", tags=["syntexa-model"])

# Tentar carregar modelo treinado
_model = None
_tokenizer = None
_cfg = None
_device = None

def _load_model():
    global _model, _tokenizer, _cfg, _device
    if _model is not None:
        return True
    try:
        root = Path(__file__).resolve().parents[3]
        ckpt = root / "checkpoints" / "syntexa_local" / "final"
        if not ckpt.exists():
            return False

        sys.path.insert(0, str(root))
        from vereda_ai.syntexa_core.foundation_model import SyntexaFoundationModel, SyntexaFoundationConfig
        from vereda_ai.syntexa_core.foundation_tokenizer import SyntexaFoundationTokenizer

        cfg_dict = json.loads((ckpt / "config.json").read_text())
        _cfg = SyntexaFoundationConfig(**cfg_dict)
        _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        _model = SyntexaFoundationModel(_cfg)
        _model.load_state_dict(torch.load(ckpt / "model.pt", map_location=_device))
        _model.to(_device)
        _model.eval()
        _tokenizer = SyntexaFoundationTokenizer.load(ckpt / "tokenizer")
        return True
    except Exception:
        return False


class ChatRequest(BaseModel):
    message: str
    max_tokens: int = 64
    temperature: float = 0.8


class ChatResponse(BaseModel):
    response: str
    model: str
    tokens_generated: int


@router.post("/chat", response_model=ChatResponse)
async def model_chat(req: ChatRequest):
    if not _load_model():
        raise HTTPException(status_code=503, detail="Modelo nao carregado. Verifique se o checkpoint existe.")

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
        return ChatResponse(response=text, model="syntexa_30m", tokens_generated=tokens)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na geracao: {e}")


@router.get("/status")
async def model_status():
    loaded = _load_model()
    return {
        "model_loaded": loaded,
        "model_name": "syntexa_30m" if loaded else None,
        "device": str(_device) if loaded else None,
        "params": sum(p.numel() for p in _model.parameters()) if loaded else None,
    }
