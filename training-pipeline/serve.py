#!/usr/bin/env python3
"""Servidor de inferência Syntexa — vLLM / Ollama / Native"""
import argparse, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from vereda_ai.syntexa_core.foundation_model import SyntexaFoundationModel
from vereda_ai.syntexa_core.foundation_tokenizer import SyntexaFoundationTokenizer
from vereda_ai.syntexa_core.foundation_inference import generate_stream

ap = argparse.ArgumentParser()
ap.add_argument("--checkpoint", required=True)
ap.add_argument("--tokenizer", required=True)
ap.add_argument("--port", type=int, default=8000)
ap.add_argument("--host", default="0.0.0.0")
ap.add_argument("--quantization", choices=["none", "4bit", "8bit"], default="none")
args = ap.parse_args()

print("[Syntexa Serve] Carregando modelo...")
tok = SyntexaFoundationTokenizer.load(args.tokenizer)
model = SyntexaFoundationModel.load(args.checkpoint)
model.eval()
print(f"[Syntexa Serve] Pronto em {args.host}:{args.port}")

# FastAPI endpoint simples
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
app = FastAPI()

@app.post("/v1/chat/completions")
def chat(req: dict):
    msgs = req.get("messages", [])
    temp = req.get("temperature", 0.7)
    max_tok = req.get("max_tokens", 512)
    stream = req.get("stream", False)
    if stream:
        return StreamingResponse(
            (f"data: {json.dumps({'choices':[{'delta':{'content':c}}]})}\n\n" for c in generate_stream(model, tok, msgs, temperature=temp, max_new_tokens=max_tok)),
            media_type="text/event-stream"
        )
    reply = ""
    for chunk in generate_stream(model, tok, msgs, temperature=temp, max_new_tokens=max_tok):
        reply += chunk
    return {"choices": [{"message": {"content": reply}}]}

@app.get("/health")
def health():
    return {"status": "ok", "model": "syntexa_native"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port)
