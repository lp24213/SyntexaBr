# Syntexa Split Architecture — Railway Gateway + AI Workers

## Causa Raiz dos Problemas

O sistema falhava no Railway porque:

1. **Startup pesado**: `vereda_backend/ai_runtime.py` carregava torch, transformers, fastembed, sentence-transformers no **import do módulo** — ou seja, no boot do container.
2. **Healthcheck lento**: `GET /health` acessava DB, Redis, Stripe, LLM e Quantum Orchestrator. Railway matou o container antes dele responder.
3. **Container gigante**: requirements.txt incluía torch, transformers, onnxruntime, scipy pesado, etc. Build travava, RAM explodia, cold boot era absurdo.
4. **Railway timeout**: Container demorava >60s para iniciar. Railway considerava unhealthy e reiniciava em loop.

## Solução: Arquitetura Split

### 1. Gateway API (Railway) — `vereda_backend` + `Dockerfile.railway`
- **FastAPI leve** sem IA pesada
- **Healthcheck instantâneo** (`GET /health` → `{"status":"ok"}` em <1ms)
- **NÃO carrega** torch, transformers, fastembed, onnxruntime, whisper, huggingface
- **Proxy reverso** para AI Worker (Kaggle/GPU) e Local Private AI (Ollama)
- **Dependências mínimas**: fastapi, uvicorn, sqlalchemy, pydantic, stripe, redis, httpx
- **Modo Gateway**: `GATEWAY_MODE=true` no `.env`
- **Startup**: <10 segundos

### 2. AI Worker (Kaggle / GPU Externo) — `infrastructure/ai-worker/`
- **Microserviço separado** na porta 8001
- **Lazy loading**: modelos só são carregados na primeira requisição
- **Endpoints**: chat completions, embeddings, OCR, TTS, STT, rerank
- **Dependências pesadas**: torch, transformers, fastembed, onnxruntime, whisper, opencv, easyocr, TTS

### 3. Local Private AI (Servidor Local) — `infrastructure/local-private-ai/`
- **Integração com Ollama** na porta 8002
- **Modelos privados**, automações internas, inferência sigilosa
- **Dependências leves**: apenas httpx + FastAPI (fala com Ollama via HTTP)

## Árvore de Pastas

```
syntexabr/
├── vereda_backend/              # Gateway (modificado)
│   ├── main.py                  # Startup leve, GATEWAY_MODE condicional
│   ├── ai_runtime.py            # LAZY LOADING (não carrega no import)
│   ├── core/
│   │   ├── config.py            # + gateway_mode, ai_worker_url, local_ai_url
│   │   ├── ai_proxy_client.py   # Cliente HTTP para workers externos
│   │   ├── lazy_loader.py       # Registry de lazy loading
│   │   └── ...
│   ├── services/
│   │   └── autonomy_manager.py  # Lazy import de agent_system
│   └── api/v1/endpoints/
│       └── health.py            # /health instantâneo, /health/detailed completo
│
├── infrastructure/
│   ├── gateway-api/               # Gateway standalone (opcional)
│   │   ├── main.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── ai_proxy.py
│   │   └── api/
│   │
│   ├── ai-worker/                 # Serviço de IA pesada
│   │   ├── main.py
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── engines.py         # Lazy loading de modelos
│   │   └── api/v1/endpoints/
│   │       ├── chat.py
│   │       ├── embeddings.py
│   │       ├── ocr.py
│   │       ├── tts.py
│   │       └── stt.py
│   │
│   └── local-private-ai/          # Serviço local (Ollama)
│       ├── main.py
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── core/
│       │   ├── config.py
│       │   └── ollama_client.py
│       └── api/v1/endpoints/
│           ├── chat.py
│           └── embeddings.py
│
├── Dockerfile.railway             # Container leve para Railway
├── requirements.railway.txt     # Dependências mínimas (sem IA)
├── docker-compose.split.yml     # Orquestração dos 3 serviços
└── railway.json                 # Aponta para Dockerfile.railway
```

## Dockerfiles

### Railway Gateway (`Dockerfile.railway`)
- Base: `python:3.12-slim-bookworm`
- Instala apenas `requirements.railway.txt`
- Copia apenas código do gateway (vereda_backend)
- Healthcheck rápido (15s interval, 3s timeout, 5s start-period)
- `GATEWAY_MODE=true` no ENV

### AI Worker (`infrastructure/ai-worker/Dockerfile`)
- Base: `python:3.12-slim-bookworm`
- Instala `requirements-ai.txt` (torch, transformers, fastembed, etc.)
- Porta 8001
- Healthcheck com start-period de 120s (tempo para carregar modelos)

### Local Private AI (`infrastructure/local-private-ai/Dockerfile`)
- Base: `python:3.12-slim-bookworm`
- Apenas httpx + FastAPI
- Porta 8002

## Regras Absolutas

1. **Railway inicia em <10s**: `GATEWAY_MODE=true` desativa carregamento de IA no startup.
2. **Startup NÃO carrega IA**: `ai_runtime.py` usa lazy factories. `autonomy_manager.py` usa lazy import.
3. **`GET /health` responde instantaneamente**: zero acesso a DB/Redis/Stripe/IA/Kaggle.
4. **Modelos IA são lazy-loading**: só carregam na primeira requisição real.
5. **Toda IA pesada sai do Railway**: embeddings, LLM, OCR, TTS, STT, rerank → AI Worker.

## Variáveis de Ambiente

```bash
# Railway Gateway
GATEWAY_MODE=true
AI_WORKER_URL=https://ai-worker.seu-dominio.com
AI_WORKER_API_KEY=...
LOCAL_AI_URL=http://10.0.0.5:8002
LOCAL_AI_API_KEY=...

# AI Worker
AI_WORKER_API_KEY=...
EMBEDDING_BACKEND=fastembed
FASTEMBED_MODEL_NAME=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
DEFAULT_LLM_MODEL=microsoft/DialoGPT-medium
WHISPER_MODEL_SIZE=base

# Local Private AI
OLLAMA_ENDPOINT=http://localhost:11434
OLLAMA_DEFAULT_MODEL=llama3
LOCAL_AI_API_KEY=...
```

## Comunicação entre Serviços

```
Client → Cloudflare → Railway Gateway (8000)
    ├── Proxy HTTP → AI Worker (8001) [Kaggle/GPU]
    ├── Proxy HTTP → Local Private AI (8002) [Ollama]
    └── Responde direto: auth, pagamentos, admin, health
```

- Gateway usa `httpx` com retry (3x, backoff exponencial)
- Timeouts: 120s para chat, 60s para embeddings/media
- Circuit breaker implícito: se worker falha, gateway retorna 502

## Deploy

### Railway (Gateway)
```bash
# railway.json já aponta para Dockerfile.railway
railway up
```

### Kaggle (AI Worker)
```bash
# Notebook Kaggle: expõe API via ngrok/cloudflared
# ou VM dedicada
docker build -f infrastructure/ai-worker/Dockerfile -t syntexa-ai-worker .
docker run -p 8001:8001 --gpus all syntexa-ai-worker
```

### Local (Private AI)
```bash
docker build -f infrastructure/local-private-ai/Dockerfile -t syntexa-local-ai .
docker run -p 8002:8002 --env OLLAMA_ENDPOINT=http://host.docker.internal:11434 syntexa-local-ai
```

### Tudo junto (dev)
```bash
docker-compose -f docker-compose.split.yml up
```

## O que foi removido do Railway

- ❌ fastembed
- ❌ onnxruntime
- ❌ scipy pesado
- ❌ huggingface (transformers, tokenizers, accelerate)
- ❌ torch
- ❌ tensorflow
- ❌ sentence-transformers
- ❌ whisper
- ❌ TTS / piper-tts
- ❌ opencv-python
- ❌ GPUtil / nvidia-ml-py
- ❌ bitsandbytes / trl / peft

## O que ficou no Railway

- ✅ FastAPI + uvicorn
- ✅ pydantic + pydantic-settings
- ✅ sqlalchemy + psycopg2-binary
- ✅ auth (python-jose, passlib, bcrypt)
- ✅ stripe
- ✅ redis (leve, cache/pubsub)
- ✅ httpx (proxy para workers)
- ✅ websockets
- ✅ structlog / prometheus / opentelemetry
