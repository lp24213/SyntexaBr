#!/usr/bin/env python3
"""
Servidor de inferência Syntexa na AWS.
Endpoint: POST /generate
Payload: {"messages": [{"role":"user","content":"..."}], "max_new_tokens": 50}
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "/opt/syntexa")

import torch
from foundation_model import SyntexaFoundationModel, SyntexaFoundationConfig
from foundation_tokenizer import SyntexaFoundationTokenizer
from foundation_inference import SyntexaInferenceEngine

# Carrega modelo
CKPT_DIR = Path("/opt/syntexa")
print("[SERVER] Carregando tokenizer...")
tokenizer = SyntexaFoundationTokenizer.load(CKPT_DIR / "tokenizer")
print(f"[SERVER] Tokenizer OK: vocab={tokenizer.vocab_size}")

print("[SERVER] Carregando config...")
with open(CKPT_DIR / "config.json") as f:
    cfg_dict = json.load(f)
cfg_dict.pop("dtype", None)
cfg = SyntexaFoundationConfig(**cfg_dict)
print(f"[SERVER] Config: dim={cfg.dim}, layers={cfg.num_layers}")

print("[SERVER] Criando modelo...")
model = SyntexaFoundationModel(cfg)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)
print(f"[SERVER] Device: {device}")

print("[SERVER] Carregando pesos...")
state = torch.load(CKPT_DIR / "model.pt", map_location=device)
model.load_state_dict(state, strict=False)
model.eval()
print("[SERVER] Modelo pronto!")

# Engine de inferência
engine = SyntexaInferenceEngine()
engine._model = model
engine._tokenizer = tokenizer
engine.device = device
engine.dtype = torch.float32

# Servidor HTTP simples
from http.server import HTTPServer, BaseHTTPRequestHandler

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/generate":
            self.send_error(404)
            return
        
        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len)
        req = json.loads(body.decode('utf-8'))
        
        messages = req.get("messages", [])
        max_new = req.get("max_new_tokens", 30)
        temp = req.get("temperature", 0.7)
        
        try:
            resp = engine.chat(messages, max_new_tokens=max_new, temperature=temp)
            result = {"response": resp, "status": "ok"}
        except Exception as e:
            result = {"error": str(e), "status": "error"}
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode('utf-8'))
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "model": "syntexa", "params": sum(p.numel() for p in model.parameters())}).encode())
        else:
            self.send_error(404)
    
    def log_message(self, fmt, *args):
        pass  # Silencia logs

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"[SERVER] Iniciando em porta {port}...")
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"[SERVER] Pronto! http://0.0.0.0:{port}")
    server.serve_forever()
