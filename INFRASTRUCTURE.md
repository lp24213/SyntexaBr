# Syntexa Sovereign AI — Arquitetura de Infraestrutura

## Divisão: Local / Railway / Kaggle

---

## 1. RAILWAY (Backend Principal — Produção)

**URL:** `api.syntexabr.com.br` → aponta para Railway

**O que roda no Railway:**
- FastAPI Backend (vereda_backend)
- PostgreSQL (Railway provisiona automaticamente)
- Redis (Railway provisiona automaticamente)
- vereda_ai runtime (LLM Engine, Agent System, Memory)
- Quantum Orchestrator
- API v1 completa (chat, auth, agents, streaming)

**Vantagens:**
- Deploy automático via GitHub
- HTTPS gratuito + certificado auto-renovado
- PostgreSQL gerenciado (backups automáticos)
- Redis gerenciado
- Escalabilidade horizontal (aumentar replicas)

**Limitações:**
- Sem GPU (CPU apenas para inference leve)
- Para LLM pesado, delegar ao Local ou Kaggle

---

## 2. LOCAL (Inference Pesada + GPU)

**URL:** `localhost:8001` ou IP da máquina local

**O que roda local:**
- Modelo Syntexa próprio (GPU NVIDIA)
- Ollama (modelos locais: Qwen, DeepSeek, Mistral)
- llama.cpp server
- ONNX Runtime / TensorRT models
- Redis local para cache

**Vantagens:**
- GPU NVIDIA dedicada (RTX 4090, A6000, etc.)
- Zero custo de inferência (próprio hardware)
- Controle total dos modelos
- Dados não saem da máquina

**Conexão com Railway:**
- Local expõe API na porta 8001
- Railway aponta `LOCAL_LLM_ENDPOINT` para IP público da máquina local (ou VPN/tunnel)

---

## 3. KAGGLE (Fine-Tuning + Training)

**URL:** Kaggle Notebooks (GPU T4/P100/A100)

**O que roda no Kaggle:**
- Fine-tuning Syntexa (QLoRA, PEFT, Flash Attention)
- Training pipeline completo
- Dataset synthesis
- Model export (GGUF, Ollama format)
- Benchmarks

**Vantagens:**
- GPU gratuita (T4/P100) por 12h/semana
- A100 disponível (custo por hora)
- Ambiente Jupyter pré-configurado
- Datasets públicos/privados

**Output:**
- Adapters LoRA exportados
- Modelos GGUF para Ollama
- Checkpoints para deploy local

---

## Fluxo de Dados

```
Usuário → Cloudflare (frontend) → Railway API (8000)
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
              PostgreSQL             Redis Cache          Local GPU
              (dados)                (sessões)            (inference pesada)
                    │                    │                    │
                    │              ┌─────┴─────┐              │
                    │              │           │              │
                    │              ▼           ▼              │
                    │         Agent System   Memory           │
                    │              │           │              │
                    └──────────────┴───────────┴──────────────┘
                                   │
                                   ▼
                          Quantum Orchestrator
                          (routing decisions)
                                   │
                    ┌──────────────┴──────────────┐
                    ▼                              ▼
             Kaggle (training)               Local (inference)
             - Fine-tuning                   - Modelos GGUF
             - Dataset gen                   - Ollama
             - Adapters                     - llama.cpp
```

---

## Variáveis de Ambiente (Railway)

Configure no painel do Railway:

```
DATABASE_URL=${{Postgres.DATABASE_URL}}
REDIS_URL=${{Redis.REDIS_URL}}

# Endpoints externos (seu local GPU)
OLLAMA_ENDPOINT=http://seu-ip-local:11434
LOCAL_LLM_ENDPOINT=http://seu-ip-local:8001
AZURE_TGI_ENDPOINT=https://seu-endpoint-azure.openai.azure.com

# Security
VEREDA_SECRET_KEY=<gerar-256-bit>
VEREDA_ADMIN_EMAIL=admin@syntexabr.com.br
VEREDA_ADMIN_PASSWORD=<senha-forte>

# LLM
DEFAULT_LLM=syntexa_native
LOCAL_HTTP_LLM_MODEL=syntexa_small

# Feature flags
AUTONOMY_EVOLUTION_LOOP_ENABLED=true
CHAT_STRICT_REAL_PROVIDERS=false
```

---

## Deploy Railway — Passo a Passo

### 1. Criar conta
- Acesse https://railway.app
- Login com GitHub
- Crie projeto "syntexa-backend"

### 2. Conectar repositório
- No Railway dashboard: New Project → Deploy from GitHub repo
- Selecione `luisp/SyntexaBr`
- Railway detecta automaticamente o `railway.toml`

### 3. Provisionar bancos
- New → Database → Add PostgreSQL
- New → Database → Add Redis
- Variáveis são injetadas automaticamente

### 4. Configurar variáveis
- Project → Variables → adicione as variáveis acima

### 5. Deploy
- Cada push na branch `main` dispara deploy automático
- URL gerada: `https://syntexa-backend.up.railway.app`
- Configure Cloudflare Worker para apontar `api.syntexabr.com.br` para Railway

---

## Deploy Local — Passo a Passo

### Pré-requisitos
- NVIDIA GPU com CUDA 12+
- Docker + NVIDIA Container Toolkit
- Ollama instalado

### Comandos
```bash
# 1. Sobe Ollama com GPU
docker run -d --gpus all -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama

# 2. Baixa modelos
ollama pull qwen2.5:7b
ollama pull deepseek-r1:7b

# 3. Syntexa modelo próprio
cd syntexabr
docker-compose -f docker-compose.own-model-full.yml up -d

# 4. Verifica saúde
curl http://localhost:8000/health
curl http://localhost:9000/health  # own-model
curl http://localhost:11434/api/tags  # ollama
```

---

## Kaggle — Passo a Passo

### 1. Acessar
- https://www.kaggle.com
- Seu token: `KGAT_32bf149f0788658d585211527ecb69ab`

### 2. Notebook
- Abrir `syntexa_sovereign_ai.ipynb`
- Escolher GPU T4 ou P100
- Rodar todas as células

### 3. Exportar modelo
- Notebook gera adapters LoRA
- Faz download dos arquivos
- Copia para pasta `checkpoints/` do projeto local

---

## Status Atual

| Componente | Status | Onde |
|------------|--------|------|
| Backend API | ✅ Funcionando | Local (8000) |
| Frontend | ✅ No ar | Cloudflare Pages |
| Gateway Worker | ✅ No ar | Cloudflare Workers |
| Database | ✅ SQLite | Local |
| Redis | ⚠️ Não configurado | Precisa subir |
| Ollama | ⚠️ Não configurado | Precisa subir |
| Own Model | ⚠️ Não treinado | Precisa treinar no Kaggle |
| Railway Deploy | 🔄 Pronto para subir | Aguardando login |

---

## Próximos Passos Imediatos

1. **Fazer login no Railway** → https://railway.app
2. **Criar projeto** e conectar GitHub repo
3. **Adicionar PostgreSQL + Redis**
4. **Fazer push do código** (com railway.toml)
5. **Configurar variáveis de ambiente**
6. **Apontar Cloudflare Worker** para URL do Railway
7. **Subir Local GPU** com Ollama + modelos
8. **Treinar no Kaggle** e exportar modelo
