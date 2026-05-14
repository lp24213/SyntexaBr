# Syntexa AI Worker - Kaggle GPU Edition (Cloudflared Tunnel)
# URL FIXA E PERMANENTE - nao muda quando reinicia

# === INSTALACAO ===
import subprocess, sys, time, os

packages = ["fastapi", "uvicorn", "httpx", "transformers", "accelerate", "sentence-transformers"]
for pkg in packages:
    for attempt in range(3):
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "--timeout", "300", pkg])
            print(f"OK: {pkg}")
            break
        except Exception as exc:
            print(f"ERRO {pkg} (tentativa {attempt+1}/3): {exc}")
            time.sleep(5)

# Instalar cloudflared
!wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -O /tmp/cloudflared
!chmod +x /tmp/cloudflared

# === SERVIDOR FASTAPI ===
import logging
import threading
from contextlib import asynccontextmanager
from typing import Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_embed_lock = threading.Lock()
_llm_lock = threading.Lock()
_embed_model: Any = None
_llm_pipeline: Any = None

def get_embed_engine() -> Any:
    global _embed_model
    if _embed_model is not None:
        return _embed_model
    with _embed_lock:
        if _embed_model is not None:
            return _embed_model
        try:
            from sentence_transformers import SentenceTransformer
            _embed_model = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
            logger.info("Embeddings loaded")
        except Exception as exc:
            logger.error("Embeddings failed: %s", exc)
            raise
    return _embed_model

def embed_texts(texts: list[str]) -> list[list[float]]:
    engine = get_embed_engine()
    vectors = engine.encode(texts, convert_to_numpy=True)
    return [vec.tolist() for vec in vectors]

def get_llm_pipeline() -> Any:
    global _llm_pipeline
    if _llm_pipeline is not None:
        return _llm_pipeline
    with _llm_lock:
        if _llm_pipeline is not None:
            return _llm_pipeline
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
            model_name = "microsoft/DialoGPT-medium"
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info("Loading LLM on %s...", device)
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                device_map="auto" if device == "cuda" else None,
            )
            _llm_pipeline = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                device=0 if device == "cuda" else -1,
            )
            logger.info("LLM loaded")
        except Exception as exc:
            logger.error("LLM failed: %s", exc)
            raise
    return _llm_pipeline

def generate_text(messages, *, temperature=0.7, max_tokens=2048):
    pipe = get_llm_pipeline()
    prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
    result = pipe(prompt, max_new_tokens=max_tokens, temperature=temperature, do_sample=True, return_full_text=False)
    return result[0]["generated_text"].strip()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("AI Worker started")
    yield
    logger.info("AI Worker stopped")

app = FastAPI(title="Syntexa AI", version="2.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
def health():
    return {"status": "ok", "service": "syntexa-ai"}

class ChatRequest(BaseModel):
    messages: list[dict[str, str]]
    model: str | None = "default"
    temperature: float = 0.7
    max_tokens: int = 2048

@app.post("/v1/chat/completions")
def chat(req: ChatRequest):
    try:
        text = generate_text(req.messages, temperature=req.temperature, max_tokens=req.max_tokens)
        return {"choices": [{"message": {"role": "assistant", "content": text}, "finish_reason": "stop", "index": 0}], "model": req.model or "default"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Generation failed: {exc}")

class EmbedRequest(BaseModel):
    texts: list[str]
    model: str | None = "default"

@app.post("/v1/embeddings")
def embed(req: EmbedRequest):
    try:
        vectors = embed_texts(req.texts)
        return {"data": [{"index": i, "embedding": vec, "object": "embedding"} for i, vec in enumerate(vectors)], "model": req.model or "default"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {exc}")

# === INICIAR SERVIDOR + TUNNEL FIXO ===
import uvicorn
import nest_asyncio
nest_asyncio.apply()

# Iniciar servidor em thread separada
import threading
server_thread = threading.Thread(
    target=lambda: uvicorn.run(app, host="0.0.0.0", port=8001, log_level="warning"),
    daemon=True
)
server_thread.start()
print("Servidor iniciado na porta 8001")

# Iniciar Cloudflare Tunnel com URL FIXA
# Substitua SEU_TOKEN_AQUI pelo token do tunnel (criado no dashboard Cloudflare)
import subprocess as sp
print("Iniciando Cloudflare Tunnel...")
print("URL fixa: https://syntexa-ai.luispl.workers.dev (ou a que voce configurou)")

# Para criar o tunnel:
# 1. Instale cloudflared local: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/get-started/create-local-tunnel/
# 2. Rode: cloudflared tunnel login
# 3. Rode: cloudflared tunnel create syntexa-ai
# 4. Copie o token e cole abaixo:

# Descomente e configure com seu token:
# tunnel_token = "SEU_TOKEN_AQUI"
# os.environ["TUNNEL_TOKEN"] = tunnel_token
# !/tmp/cloudflared access tcp --hostname syntexa-ai.luispl.workers.dev --url localhost:8001

print("=" * 60)
print("PARA TUNNEL FIXO:")
print("1. Crie tunnel em: https://one.dash.cloudflare.com/")
print("2. Copie o token e substitua SEU_TOKEN_AQUI acima")
print("3. A URL sera fixa e permanente!")
print("=" * 60)
