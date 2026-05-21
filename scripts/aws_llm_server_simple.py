#!/usr/bin/env python3
"""
Servidor de inferência Syntexa na AWS (standalone).
Endpoint: POST /generate
Payload: {"messages": [{"role":"user","content":"..."}], "max_new_tokens": 50}
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "/opt/syntexa")

import torch
import torch.nn.functional as F

from foundation_model import SyntexaFoundationModel, SyntexaFoundationConfig
from foundation_tokenizer import SyntexaFoundationTokenizer

# Carrega modelo
CKPT_DIR = Path("/opt/syntexa")
print("[SERVER] Carregando tokenizer...", flush=True)
tokenizer = SyntexaFoundationTokenizer.load(CKPT_DIR / "tokenizer")
print(f"[SERVER] Tokenizer OK: vocab={tokenizer.vocab_size}")

print("[SERVER] Carregando config...", flush=True)
with open(CKPT_DIR / "config.json") as f:
    cfg_dict = json.load(f)
cfg_dict.pop("dtype", None)
cfg = SyntexaFoundationConfig(**cfg_dict)
print(f"[SERVER] Config: dim={cfg.dim}, layers={cfg.num_layers}")

print("[SERVER] Criando modelo...", flush=True)
model = SyntexaFoundationModel(cfg)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = model.to(device)
print(f"[SERVER] Device: {device}")

print("[SERVER] Carregando pesos...", flush=True)
state = torch.load(CKPT_DIR / "model.pt", map_location=device)
model.load_state_dict(state, strict=False)
model.eval()
print("[SERVER] Modelo pronto!")

# Otimizações CPU
torch.set_num_threads(1)

SPECIAL_TOKENS = {"<pad>": 0, "<unk>": 1, "<bos>": 2, "<eos>": 3}
EOS_ID = SPECIAL_TOKENS["<eos>"]

def format_chat(messages):
    parts = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        if role == "system":
            parts.append(f"Sistema: {content}")
        elif role == "user":
            parts.append(f"Usuario: {content}")
        else:
            parts.append(f"Assistente: {content}")
    parts.append("Assistente:")
    return "\n".join(parts)

def generate(messages, max_new_tokens=20, temperature=1.0, top_k=1):
    """Greedy decoding (top_k=1) = mais rápido em CPU."""
    prompt = format_chat(messages)
    input_ids = tokenizer.encode(prompt, add_special_tokens=True)
    if len(input_ids) > cfg.max_seq_len - max_new_tokens:
        input_ids = input_ids[-(cfg.max_seq_len - max_new_tokens):]
    
    input_tensor = torch.tensor([input_ids], dtype=torch.long, device=device)
    generated = []
    
    with torch.no_grad():
        for _ in range(max_new_tokens):
            logits, _ = model(input_tensor)
            # Greedy: pega o token com maior probabilidade
            next_token = int(torch.argmax(logits[0, -1, :]))
            
            if next_token == EOS_ID:
                break
            generated.append(next_token)
            # Evita reconstruir tensor a cada passo
            input_tensor = torch.cat([
                input_tensor,
                torch.tensor([[next_token]], dtype=torch.long, device=device)
            ], dim=1)
            if input_tensor.size(1) >= cfg.max_seq_len:
                break
    
    return tokenizer.decode(generated) if hasattr(tokenizer, 'decode') and generated else ""

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
            resp = generate(messages, max_new_tokens=max_new, temperature=temp)
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
        pass

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"[SERVER] Iniciando em porta {port}...")
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"[SERVER] Pronto! http://0.0.0.0:{port}")
    server.serve_forever()
