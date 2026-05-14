# VEREDA / SYNTEXA — Arquitetura Híbrida Soberana v3.0

> **Status:** Draft para implementação  
> **Objetivo:** Infraestrutura nível OpenAI/Anthropic/xAI/Perplexity  
> **Filosofia:** IA soberana, multimodal, híbrida cloud+local, edge-first, zero dependência de APIs externas.

---

## 1. VISÃO GERAL

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLOUDFLARE EDGE NETWORK                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐       │
│  │  Edge POP   │  │  Edge POP   │  │  Edge POP   │  │  Edge POP   │       │
│  │   São Paulo │  │   Miami     │  │   London    │  │   Singapore │       │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘       │
└─────────┼────────────────┼────────────────┼────────────────┼───────────────┘
          │                │                │                │
          └────────────────┴────────────────┴────────────────┘
                               │
                    ┌────────────▼────────────┐
                    │  CLOUDFLARE WORKERS     │
                    │  ==================     │
                    │  • Edge Auth (JWT/HMAC) │
                    │  • WAF + Anti-DDoS      │
                    │  • Rate Limiting        │
                    │  • Smart Routing        │
                    │  • Request Signing      │
                    │  • Session Validation   │
                    │  • Zero Trust Gateway   │
                    │  • WebSocket Bridge     │
                    └────────────┬────────────┘
                                 │
            ┌────────────────────┼────────────────────┐
            │                    │                    │
    ┌───────▼────────┐  ┌──────▼───────┐  ┌─────────▼──────────┐
    │  RAILWAY CORE  │  │  AWS GPU     │  │  INFRA LOCAL       │
    │  ============  │  │  CLUSTER     │  │  (Fallback/Edge)   │
    │  • FastAPI     │  │  ==========  │  │  • RTX Local       │
    │  • Auth/OAuth  │  │  • CUDA      │  │  • Ollama          │
    │  • Billing     │  │  • TensorRT  │  │  • llama.cpp       │
    │  • PostgreSQL  │  │  • vLLM      │  │  • ONNX Runtime    │
    │  • Redis       │  │  • TGI       │  │  • Redis Local     │
    │  • Queue Mgr   │  │  • Embeddings│  │  • Edge Inference  │
    │  • Agents      │  │  • OCR/Voice │  │  • Backup Queue    │
    └───────┬────────┘  └──────┬───────┘  └─────────┬──────────┘
            │                  │                      │
            └──────────────────┼──────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │   VEREDA CORE AI    │
                    │   ==============    │
                    │  • AI Router        │
                    │  • Orchestrator     │
                    │  • Multi-Agent      │
                    │  • Memory Engine    │
                    │  • Streaming Mgr    │
                    │  • Voice Pipeline   │
                    │  • Document Mgr     │
                    └─────────────────────┘
```

---

## 2. PRINCÍPIOS ARQUITETURAIS

1. **Soberania Total:** Nenhuma dependência primária de OpenAI, Azure, Ollama, Qwen, Llama ou APIs externas.
2. **Edge-First:** Cloudflare Workers é a ÚNICA entrada pública. AWS e Railway NUNCA expostos diretamente.
3. **Separação de Responsabilidades:**
   - **Workers:** Segurança, roteamento, cache edge.
   - **Railway:** Orquestração, estado, usuários, billing.
   - **AWS GPU:** Inferência pesada, embeddings, training.
   - **Local:** Fallback, inferência edge, ambiente offline.
4. **Lazy Loading:** Modelos só carregam na primeira requisição real.
5. **Circuit Breaker + Failover Automático:** Se AWS cair → local. Se local cair → queue + retry.
6. **Streaming Primeiro:** Todas as respostas IA são token-by-token.
7. **Observabilidade Total:** Métricas, traces, logs em todos os níveis.

---

## 3. FLUXO DE REDE DETALHADO

```
USUÁRIO (Browser/App/Desktop)
│
▼
[DNS] syntexabr.com.br → Cloudflare Anycast
│
▼
┌─────────────────────────────────────────┐
│ CLOUDFLARE WORKERS (Global Edge)          │
│ ─────────────────────────────────────     │
│ 1. WAF Check (IP reputation, bot fight) │
│ 2. Rate Limit (bucket por user/IP)      │
│ 3. JWT Validation (edge-auth)            │
│ 4. HMAC Verification (request signing)  │
│ 5. Session Validation (Redis KV edge)   │
│ 6. Smart Routing Decision               │
└─────────────────────────────────────────┘
│
├─ /v1/public/*  ──→  Railway (sem auth)
├─ /v1/auth/*    ──→  Railway Auth Service
├─ /v1/chat/*    ──→  Railway → AI Router → AWS GPU / Local
├─ /v1/voice/*   ──→  Railway → Voice Pipeline → AWS GPU / Local
├─ /v1/vision/*  ──→  Railway → Vision Pipeline → AWS GPU
├─ /v1/document/* ──→ Railway → Document Engine → AWS GPU
├─ /v1/agent/*   ──→  Railway → Agent System → AWS GPU / Local
├─ /v1/stream/*  ──→  Railway → Streaming Mgr → WebSocket/ SSE
├─ /ws/*         ──→  Railway WebSocket Gateway
├─ /health       ──→  Railway (instantâneo)
└─ /*            ──→  Cloudflare Pages (Next.js Frontend)
```

### 3.1 Regras de Roteamento Inteligente

| Tipo de Requisição | Destino Primário | Destino Fallback | Lógica |
|---|---|---|---|
| Chat texto | AWS GPU (g5.2xlarge) | Local RTX | Latência < 2s |
| Chat streaming | AWS GPU + SSE | Local + SSE | Token-by-token |
| Embeddings | AWS GPU | Local | Batch queue |
| OCR / Vision | AWS GPU | Local (CPU) | GPU required |
| STT / TTS | AWS GPU | Local | Voice pipeline |
| Document parse | AWS GPU | Local | File size > 10MB → AWS |
| Agent tasks | AWS GPU | Local | Complexidade |
| Training | AWS GPU (p4d) | — | Offline only |

---

## 4. ESTRUTURA DE PASTAS

```
syntexabr/
├── .github/workflows/           # CI/CD pipelines
│   ├── deploy-workers.yml
│   ├── deploy-railway.yml
│   ├── deploy-aws-gpu.yml
│   └── test-suite.yml
│
├── cloudflare-workers/          # EDGE GATEWAY (única entrada pública)
│   ├── src/
│   │   ├── index.js             # Worker principal (gateway)
│   │   ├── auth.js              # JWT + HMAC edge validation
│   │   ├── routing.js           # Smart router logic
│   │   ├── rate-limit.js        # Durable Objects / KV rate limit
│   │   ├── websocket.js         # WS gateway bridge
│   │   ├── cache.js             # Edge cache strategy
│   │   └── security.js          # WAF, bot fight, Zero Trust
│   ├── wrangler.toml            # Configuração Worker
│   └── package.json
│
├── vereda_backend/              # RAILWAY CORE BACKEND
│   ├── main.py                  # FastAPI gateway mode
│   ├── core/
│   │   ├── config.py            # Settings híbridos
│   │   ├── ai_proxy_client.py   # Cliente HTTP para AI Workers
│   │   ├── lazy_loader.py       # Registry lazy loading
│   │   ├── circuit_breaker.py   # Failover automático
│   │   ├── streaming_manager.py # SSE / WS streaming core
│   │   └── runtime_watchdog.py  # Health + metrics
│   ├── api/v1/
│   │   ├── endpoints/
│   │   │   ├── auth.py          # OAuth, 2FA, JWT
│   │   │   ├── chat.py          # Chat orchestration
│   │   │   ├── voice.py         # STT/TTS proxy
│   │   │   ├── vision.py        # OCR / image analysis
│   │   │   ├── document.py      # Document processing
│   │   │   ├── agent.py         # Multi-agent system
│   │   │   ├── memory.py        # Semantic memory
│   │   │   ├── search.py        # Web RAG
│   │   │   ├── export.py        # PDF/DOCX/XLSX
│   │   │   ├── health.py        # Instant + detailed
│   │   │   └── websocket.py     # WS gateway
│   │   └── routes.py            # Router aggregator
│   ├── services/
│   │   ├── ai_router.py         # AI Router Engine
│   │   ├── agent_orchestrator.py # Multi-agent coordination
│   │   ├── voice_pipeline.py    # Voice processing
│   │   ├── document_engine.py   # Document parsing
│   │   ├── streaming_engine.py  # Token streaming
│   │   ├── queue_manager.py   # Redis/RabbitMQ queue
│   │   ├── billing_service.py # Stripe integration
│   │   └── autonomy_manager.py # Self-healing + evolution
│   ├── db/
│   │   ├── models.py            # SQLAlchemy models
│   │   └── session.py           # DB session manager
│   ├── queues/
│   │   └── redis_queue.py       # Task queue + workers
│   ├── workers/
│   │   └── background_jobs.py   # Celery / RQ tasks
│   └── tests/
│
├── vereda_ai/                   # IA CORE ENGINE (soberano)
│   ├── __init__.py
│   ├── agent_system.py          # Multi-agent framework
│   ├── llm_engine.py            # Inference engine próprio
│   ├── embedding_engine.py      # Embeddings soberanos
│   ├── memory_engine.py         # Memória semântica
│   ├── reasoning_engine.py      # Chain-of-thought / ToT
│   ├── math_engine.py           # SymPy + cálculo simbólico
│   ├── code_engine.py           # Sandbox + execução segura
│   ├── voice_engine.py          # STT/TTS próprios
│   ├── vision_engine.py         # OCR + visão computacional
│   ├── multimodal_router.py     # Cross-modal reasoning
│   └── document_parser.py       # Parser inteligente
│
├── infrastructure/
│   ├── gateway-api/             # Gateway standalone (opcional)
│   │   ├── main.py
│   │   ├── Dockerfile
│   │   └── requirements.txt
│   │
│   ├── ai-worker/               # AI Worker container (Railway/Hybrid)
│   │   ├── main.py              # FastAPI com lazy loading
│   │   ├── Dockerfile
│   │   ├── requirements.txt     # torch, transformers, etc.
│   │   ├── core/
│   │   │   ├── engines.py       # Model loaders
│   │   │   └── gpu_scheduler.py # GPU task scheduler
│   │   └── api/v1/
│   │       ├── chat.py
│   │       ├── embeddings.py
│   │       ├── ocr.py
│   │       ├── tts.py
│   │       └── stt.py
│   │
│   ├── aws-gpu-cluster/         # AWS GPU CLUSTER (NOVO)
│   │   ├── docker-compose.gpu.yml
│   │   ├── Dockerfile.gpu
│   │   ├── main.py              # vLLM / TGI server
│   │   ├── requirements.gpu.txt
│   │   ├── scripts/
│   │   │   ├── setup-aws.sh     # Setup EC2 GPU
│   │   │   ├── start-cluster.sh
│   │   │   ├── health-check.sh
│   │   │   └── auto-scale.sh    # Auto-scaling logic
│   │   ├── config/
│   │   │   ├── nginx.gpu.conf   # Reverse proxy interno
│   │   │   ├── prometheus.yml   # Métricas GPU
│   │   │   └── tensorrt-config.yaml
│   │   └── systemd/
│   │       └── syntexa-gpu.service
│   │
│   ├── local-hybrid/            # INFRA LOCAL HÍBRIDA (NOVO)
│   │   ├── docker-compose.local.yml
│   │   ├── Dockerfile.local
│   │   ├── main.py              # FastAPI local inference
│   │   ├── requirements.local.txt
│   │   ├── scripts/
│   │   │   ├── start-local.sh
│   │   │   ├── fallback-sync.sh
│   │   │   └── health-check.sh
│   │   └── config/
│   │       └── ollama-bridge.yaml
│   │
│   └── shared/                  # Schemas + clients compartilhados
│       ├── schemas/
│       └── clients/
│
├── frontend/                    # NEXT.JS FRONTEND
│   ├── app/                     # App router (Next.js 14+)
│   ├── components/
│   ├── lib/
│   ├── hooks/
│   └── e2e/                     # Playwright tests
│
├── monitoring/                  # OBSERVABILIDADE
│   ├── prometheus/
│   │   ├── prometheus.yml
│   │   └── alert_rules.yml
│   ├── grafana/
│   │   └── dashboards/
│   └── alertmanager/
│       └── alertmanager.yml
│
├── security/                    # SEGURANÇA
│   ├── policies/
│   ├── guardrails/
│   └── audit/
│
├── scripts/                     # AUTOMATION
│   ├── deploy/
│   │   ├── deploy-workers.sh
│   │   ├── deploy-railway.sh
│   │   ├── deploy-aws-gpu.sh
│   │   └── deploy-all.sh
│   └── tools/
│
├── tests/                       # TESTES
│   ├── unit/
│   ├── integration/
│   ├── e2e/
│   └── stress/
│
├── docs/                        # DOCUMENTAÇÃO
│   └── VEREDA_HYBRID_ARCHITECTURE.md   # Este arquivo
│
├── docker-compose.yml           # DEV local completo
├── docker-compose.split.yml     # Split architecture (dev)
├── Dockerfile.railway           # Railway leve
├── railway.toml                 # Railway config
├── wrangler.toml                # Cloudflare Workers config
├── requirements.txt             # Python deps completas
├── requirements.railway.txt     # Railway deps mínimas
└── README.md
```

---

## 5. MICROSSERVIÇOS — RAILWAY CORE

| Serviço | Tecnologia | Porta | Responsabilidade |
|---|---|---|---|
| API Gateway | FastAPI + uvicorn | 8000 | Roteamento, orchestration |
| Auth Service | FastAPI + JWT | 8000/v1/auth | OAuth, 2FA, sessions |
| Billing Service | FastAPI + Stripe | 8000/v1/billing | Pagamentos, planos |
| AI Router | FastAPI + httpx | 8000/v1/chat | Roteia para AWS/Local |
| Agent System | FastAPI + vereda_ai | 8000/v1/agent | Multi-agent orchestration |
| Streaming Engine | FastAPI + SSE/WS | 8000/v1/stream | Token streaming |
| Voice Engine | FastAPI + proxy | 8000/v1/voice | STT/TTS pipeline |
| Vision Engine | FastAPI + proxy | 8000/v1/vision | OCR, image analysis |
| Document Engine | FastAPI + proxy | 8000/v1/document | Parse, extract, index |
| Memory Engine | FastAPI + pgvector | 8000/v1/memory | Semantic memory, RAG |
| Queue System | Redis + Python workers | — | Background jobs |
| Monitoring Core | Prometheus + Grafana | 9090/3000 | Métricas, alertas |

---

## 6. AWS GPU CLUSTER

### 6.1 Instâncias Recomendadas

| Fase | Instância | GPU | VRAM | Uso |
|---|---|---|---|---|
| Início | g5.xlarge | 1x A10G | 24 GB | Inferência leve, dev |
| Início | g5.2xlarge | 1x A10G | 24 GB | Inferência média |
| Escala Média | g5.12xlarge | 4x A10G | 96 GB | Multi-modelo, batch |
| Escala Alta | p4d.24xlarge | 8x A100 | 320 GB | Training, inference massiva |
| Escala Monstra | p5.48xlarge | 8x H100 | 640 GB | LLM 70B+, cluster multi-node |

### 6.2 Topologia do Cluster GPU

```
┌─────────────────────────────────────────────┐
│              AWS VPC (syntexa-vpc)           │
│  ┌───────────────────────────────────────┐   │
│  │  Private Subnet (GPU instances)      │   │
│  │  ─────────────────────────────────   │   │
│  │  ┌─────────┐ ┌─────────┐ ┌────────┐ │   │
│  │  │  GPU-1  │ │  GPU-2  │ │ GPU-N  │ │   │
│  │  │ vLLM    │ │ vLLM    │ │ vLLM   │ │   │
│  │  │ TensorRT│ │ TensorRT│ │ TGI    │ │   │
│  │  │ Embeddings│Embeddings│Embeddings│ │   │
│  │  │ OCR     │ │ Voice   │ │ Vision │ │   │
│  │  └────┬────┘ └────┬────┘ └───┬────┘ │   │
│  │       └───────────┼──────────┘      │   │
│  │                   │                 │   │
│  │            ┌──────▼──────┐        │   │
│  │            │  GPU LB     │        │   │
│  │            │  (NGINX)    │        │   │
│  │            └──────┬──────┘        │   │
│  └───────────────────┼───────────────┘   │
│                      │                     │
│  ┌───────────────────┼───────────────┐     │
│  │  Public Subnet (t3.micro bastion)│     │
│  │  ─────────────────────────────── │     │
│  │  ┌─────────┐  ┌─────────────┐ │     │
│  │  │Bastion  │  │ Cloudflare  │ │     │
│  │  │t3.micro │  │ Tunnel      │ │     │
│  │  │Monitor  │  │ (zero trust)│ │     │
│  │  └─────────┘  └─────────────┘ │     │
│  └───────────────────────────────┘     │
└─────────────────────────────────────────────┘
```

### 6.3 Regras AWS GPU

- **ZERO IP público** nas instâncias GPU.
- Acesso apenas via **Cloudflare Tunnel** ou **AWS SSM**.
- **t3.micro** (bastion) é o único ponto de entrada administrativa.
- GPU instances usam **NVIDIA Container Toolkit + Docker**.
- **vLLM** para LLM serving (mais rápido que TGI).
- **TensorRT-LLM** para modelos compilados.
- **Ray Serve** para orquestração multi-node (futuro).

---

## 7. INFRA LOCAL HÍBRIDA

### 7.1 Função

- **Fallback automático** se AWS sobrecarregar ou cair.
- **Inferência edge** para dados sensíveis (não saem da rede).
- **Backup de filas** quando AWS está indisponível.
- **Ambiente offline** para desenvolvimento e testes.
- **Cache distribuído** via Redis local.

### 7.2 Componentes

| Componente | Tecnologia | Porta | Uso |
|---|---|---|---|
| LLM Local | Ollama + llama.cpp | 11434 | Inferência texto |
| LLM HTTP | FastAPI local | 8002 | Proxy Ollama |
| Embeddings | sentence-transformers | 8002 | Vetores locais |
| STT | whisper.cpp | 8002 | Transcrição |
| TTS | piper / Coqui | 8002 | Síntese voz |
| Redis | redis-server | 6379 | Cache + queue |
| Sync Agent | Python script | — | Sincronização AWS ↔ Local |

### 7.3 Lógica de Failover

```python
# Pseudocódigo do AI Router
async def route_inference(request):
    # 1. Tenta AWS GPU (primário)
    if aws_gpu_healthy and aws_gpu_queue_depth < threshold:
        return await aws_gpu.inference(request)

    # 2. Fallback para local
    if local_gpu_healthy:
        return await local_gpu.inference(request)

    # 3. Queue para retry assíncrono
    await redis_queue.enqueue("inference", request)
    return {"status": "queued", "estimated_wait": "< 30s"}
```

---

## 8. PIPELINE MULTIMODAL

```
Entrada (imagem + áudio + texto + documento)
│
▼
┌─────────────────────────────┐
│  MULTIMODAL ROUTER          │
│  • Detecta tipos de mídia   │
│  • Prioriza processamento   │
│  • Decide sync vs async    │
└─────────────────────────────┘
│
├─→ Imagem ──→ Vision Engine (AWS GPU) ──→ Descrição + OCR + Detecção
├─→ Áudio ───→ Voice Pipeline (AWS GPU) ──→ STT → Texto → TTS (resposta)
├─→ Texto ───→ LLM Engine (AWS GPU/Local) ──→ Reasoning → Resposta
└─→ Documento → Document Engine (AWS GPU) ──→ Parse → Chunk → Vector Index
│
▼
┌─────────────────────────────┐
│  UNIFIED CONTEXT ENGINE       │
│  • Fusão cross-modal         │
│  • Shared memory             │
│  • Contexto persistente      │
└─────────────────────────────┘
│
▼
Streaming Response → Usuário
```

---

## 9. PIPELINE DE VOZ (SOBERANA)

```
Usuário fala (microfone / arquivo)
│
▼
┌─────────────────────────────┐
│  EDGE AUDIO GATEWAY (CF)    │
│  • WebRTC ou WebSocket       │
│  • Compressão Opus           │
│  • Rate limiting de áudio    │
└─────────────────────────────┘
│
▼
┌─────────────────────────────┐
│  STT ENGINE (Whisper CUDA)  │
│  • Modelo: whisper-large-v3 │
│  • Lang: pt/en auto-detect  │
│  • Streaming parcial         │
│  • Punctuation restore       │
└─────────────────────────────┘
│
▼
Texto ──→ VEREDA Core ──→ AI Reasoning
│
▼
┌─────────────────────────────┐
│  TTS ENGINE (Piper/Coqui)   │
│  • Modelo: pt-BR natural     │
│  • Emotion engine            │
│  • Prosody control           │
│  • Streaming chunk           │
└─────────────────────────────┘
│
▼
Streaming de voz (Opus/WebRTC) → Usuário
```

### 9.1 Requisitos Voice AI

- **Latência:** < 500ms total (STT + LLM + TTS)
- **Formatos:** Opus, MP3, WAV, PCM
- **Protocolos:** WebRTC (realtime), WebSocket (streaming), HTTP (batch)
- **Modelos STT:** Whisper large v3 (próprio), fine-tuned pt-BR
- **Modelos TTS:** Piper (leve) + Coqui TTS (qualidade) + futuro modelo próprio

---

## 10. PIPELINE DE DOCUMENTOS

```
Upload (PDF, DOCX, XLSX, PPTX, CSV, TXT, MD, HTML, ZIP)
│
▼
┌─────────────────────────────┐
│  UPLOAD VALIDATOR           │
│  • Mime-type check          │
│  • File size limit (50MB)   │
│  • Malware scan (ClamAV)    │
│  • Checksum validation      │
└─────────────────────────────┘
│
▼
┌─────────────────────────────┐
│  DOCUMENT ENGINE            │
│  • Parser inteligente        │
│  • Table extraction          │
│  • OCR híbrido (if needed)   │
│  • Metadata extraction       │
│  • Encoding preservation      │
└─────────────────────────────┘
│
▼
┌─────────────────────────────┐
│  SEMANTIC CHUNKING          │
│  • Preserve context          │
│  • Detect tables / lists     │
│  • Header hierarchy          │
│  • Overlap strategy          │
└─────────────────────────────┘
│
▼
┌─────────────────────────────┐
│  VECTOR INDEXING              │
│  • Embeddings próprios        │
│  • pgvector (PostgreSQL)      │
│  • Metadata + content         │
│  • Deduplication              │
└─────────────────────────────┘
│
▼
RAG / Chat / Search
```

### 10.1 Garantias Documentais

- **PDF:** Preserva colunas, tabelas, formatação, links.
- **XLSX:** Mantém fórmulas, formatação condicional, múltiplas sheets.
- **DOCX:** Preserva headings, lists, tables, styles.
- **Encoding:** UTF-8 obrigatório, detecção automática de charset.
- **Retry:** 3 tentativas automáticas com backoff exponencial.

---

## 11. ESTRATÉGIA DE STREAMING

### 11.1 Arquitetura Streaming

| Camada | Tecnologia | Latência Alvo |
|---|---|---|
| Edge | Cloudflare Workers + SSE | < 50ms |
| Backend | FastAPI + asyncio generators | < 100ms |
| AI Router | httpx streaming + proxy | < 200ms |
| GPU | vLLM + OpenAI-compatible streaming | < 20ms/token |
| Cliente | Next.js + EventSource / WS | — |

### 11.2 Protocolos

- **SSE (Server-Sent Events):** Para chat texto (unidirecional, simples, funciona sobre HTTP).
- **WebSocket:** Para voz realtime (bidirecional, baixa latência).
- **HTTP/2 Server Push:** Para preload de assets.

### 11.3 Fluxo Token-by-Token

```
GPU gera token → AI Router proxy → Railway FastAPI →
Cloudflare Workers SSE → Browser EventSource → DOM append
```

---

## 12. ESTRATÉGIA DE FILAS

### 12.1 Camadas de Queue

| Tipo | Tecnologia | Uso |
|---|---|---|
| Edge Queue | Cloudflare Queues | Rate limiting, buffering |
| Priority Queue | Redis Sorted Sets | Tasks prioritárias |
| Background Queue | Celery + Redis | Jobs pesados (OCR, parse, training) |
| Dead Letter Queue | Redis / PostgreSQL | Retry falhos, auditoria |

### 12.2 Tipos de Jobs

```
HIGH PRIORITY (executa imediatamente):
- Chat streaming
- Voice STT/TTS
- Health checks

MEDIUM PRIORITY (queue, < 5s):
- Embeddings
- Document parse (< 1MB)
- Memory index

LOW PRIORITY (background, async):
- Document parse (> 10MB)
- Batch embeddings
- Training pipeline
- Modelo export
- Analytics aggregation
```

---

## 13. ESTRATÉGIA DE MEMÓRIA

### 13.1 Hierarquia de Memória

| Camada | Tecnologia | Persistência | Latência |
|---|---|---|---|
| Context Window | vLLM / TGI | Volátil | < 1ms |
| Session Cache | Redis | TTL (1h) | < 5ms |
| Semantic Memory | PostgreSQL + pgvector | Persistente | < 20ms |
| Long-term Memory | PostgreSQL + embeddings | Persistente | < 50ms |
| Knowledge Base | Vector DB + RAG | Persistente | < 100ms |

### 13.2 Estratégias

- **Context Compression:** Resumir conversas longas (> 4k tokens) para manter contexto.
- **Semantic Cache:** Cachear respostas para perguntas semanticamente similares.
- **Memory Consolidation:** Agregar memórias de curto prazo em longo prazo periodicamente.
- **RAG Híbrido:** Combina busca vetorial + keyword (BM25) + reranking.

---

## 14. ESTRATÉGIA DE SEGURANÇA

### 14.1 Zero Trust Architecture

```
┌─────────────────────────────────────────┐
│  LAYER 1: EDGE (Cloudflare)             │
│  • WAF + OWASP rules                    │
│  • Bot Fight Mode + Turnstile           │
│  • DDoS protection (unmetered)          │
│  • IP reputation filtering              │
└─────────────────────────────────────────┘
│
┌─────────────────────────────────────────┐
│  LAYER 2: GATEWAY (Workers)             │
│  • JWT validation (edge)                │
│  • HMAC request signing                 │
│  • Rate limiting (per user / per IP)     │
│  • API key management                     │
│  • Session validation (KV)              │
└─────────────────────────────────────────┘
│
┌─────────────────────────────────────────┐
│  LAYER 3: ORIGIN (Railway)              │
│  • Cloudflare origin guard                │
│  • mTLS (mutual TLS)                      │
│  • Input sanitization                     │
│  • Prompt injection protection            │
│  • AI abuse detection                     │
└─────────────────────────────────────────┘
│
┌─────────────────────────────────────────┐
│  LAYER 4: DATA                          │
│  • PostgreSQL encryption at rest        │
│  • Redis AUTH + TLS                     │
│  • Backup criptografado                 │
│  • IAM mínimo (princípio do menor privilégio)
└─────────────────────────────────────────┘
```

### 14.2 AWS GPU Segurança

- **Sem IP público:** Instâncias GPU em subnet privada.
- **Acesso:** Apenas via Cloudflare Tunnel ou AWS SSM Session Manager.
- **SSH:** Desabilitado na instância GPU (usa SSM apenas).
- **Security Group:** Apenas porta 8000 do bastion interno.
- **IAM:** Role com permissões mínimas (EC2 read-only, CloudWatch logs).

### 14.3 Proteções Específicas

| Ameaça | Mitigação |
|---|---|
| Prompt Injection | Input filter + output validation + semantic analysis |
| AI Abuse | Rate limiting + usage patterns + anomaly detection |
| Data Exfiltration | Zero Trust + egress filtering + audit logs |
| Model Theft | API signing + request validation + watermarking |
| DDoS | Cloudflare (unmetered) + rate limits + circuit breaker |
| Credential Leak | JWT rotation + short-lived tokens + secret scanning |

---

## 15. ESTRATÉGIA DE DEPLOY

### 15.1 Pipeline CI/CD

```
Git Push → GitHub Actions →
├── Testes (unit + integration)
├── Lint + Type check + Security scan
├── Build containers
├── Deploy Workers (wrangler deploy)
├── Deploy Railway (railway up)
├── Deploy AWS GPU (SSM + docker pull)
└── Health check pós-deploy
```

### 15.2 Estratégia de Deploy por Componente

| Componente | Estratégia | Rollback |
|---|---|---|
| Cloudflare Workers | Blue/Green (instantâneo) | wrangler rollback |
| Railway | Rolling update | Railway revert |
| AWS GPU | Canary (10% → 50% → 100%) | DNS swap |
| Local | Rolling restart | systemd rollback |

### 15.3 Comandos de Deploy

```bash
# Deploy completo
./scripts/deploy/deploy-all.sh

# Deploy individual
./scripts/deploy/deploy-workers.sh
./scripts/deploy/deploy-railway.sh
./scripts/deploy/deploy-aws-gpu.sh
```

---

## 16. ESTRATÉGIA DE AUTO SCALING

### 16.1 Triggers

| Métrica | Threshold | Ação |
|---|---|---|
| GPU utilization | > 80% por 5min | Scale up (+1 GPU instance) |
| Queue depth | > 100 jobs | Scale up workers |
| Latency p99 | > 2s | Scale up + alert |
| Error rate | > 1% | Circuit breaker + fallback |
| Cost/hour | > budget | Alert + throttle non-priority |

### 16.2 Escala Horizontal

```
AWS GPU Cluster:
- min: 1x g5.xlarge
- max: 10x g5.12xlarge (ou p4d multi-node)
- target: 70% GPU utilization

Railway:
- min: 2 replicas
- max: 20 replicas
- target: 60% CPU / 70% memory

Workers (Queue):
- min: 2 workers
- max: 50 workers
- target: queue depth < 20
```

---

## 17. STACK TECNOLÓGICO FINAL

### 17.1 Frontend

| Tecnologia | Uso |
|---|---|
| Next.js 14+ (App Router) | Framework |
| Tailwind CSS | Styling |
| Framer Motion | Animações |
| WebSockets / SSE | Streaming |
| React Query | State management |
| Playwright | E2E tests |

### 17.2 Backend

| Tecnologia | Uso |
|---|---|
| FastAPI | API framework |
| Node.js (microservices) | Serviços específicos |
| PostgreSQL + pgvector | Banco relacional + vetores |
| Redis | Cache, sessions, queue |
| RabbitMQ (opcional) | Message broker avançado |
| Celery / RQ | Background workers |

### 17.3 AI / ML

| Tecnologia | Uso |
|---|---|
| vLLM | LLM serving |
| TensorRT-LLM | Inferência otimizada |
| Transformers (HF) | Model loading |
| Whisper | STT |
| Piper TTS / Coqui TTS | TTS |
| FastEmbed / sentence-transformers | Embeddings |
| ONNX Runtime | Modelos otimizados |
| SymPy | Matemática simbólica |
| PyMuPDF / python-docx / openpyxl | Document parsing |

### 17.4 Infraestrutura

| Tecnologia | Uso |
|---|---|
| Cloudflare Workers | Edge gateway |
| Railway | Core backend |
| AWS EC2 GPU | Cluster de inferência |
| Docker + Compose | Containerização |
| NGINX | Reverse proxy |
| Prometheus + Grafana | Observabilidade |
| Cloudflare Tunnel | Acesso privado AWS |

---

## 18. MÉTRICAS DE SUCESSO

| Métrica | Alvo Inicial | Alvo Escala |
|---|---|---|
| Latência chat (TTFT) | < 1s | < 500ms |
| Latência voz (round-trip) | < 2s | < 500ms |
| Throughput | 100 req/s | 10.000 req/s |
| Disponibilidade | 99.9% | 99.99% |
| Usuários simultâneos | 1.000 | 1.000.000+ |
| Custo por 1k tokens | $0.001 | $0.0005 |
| Tempo de deploy | 5 min | < 1 min |
| Tempo de failover | 10s | < 3s |

---

## 19. ROADMAP DE IMPLEMENTAÇÃO

### Fase 1: Foundation (Semanas 1-2)
- [ ] Refatorar Cloudflare Worker (auth, routing, WS)
- [ ] Configurar Railway com GATEWAY_MODE
- [ ] Subir AWS GPU (g5.xlarge) com vLLM
- [ ] Conectar local híbrida (Ollama)
- [ ] Pipeline básico de chat streaming

### Fase 2: Core AI (Semanas 3-4)
- [ ] AI Router com failover
- [ ] Multi-agent system
- [ ] Memory engine + RAG
- [ ] Voice pipeline (STT + TTS)
- [ ] Document engine básico

### Fase 3: Scale (Semanas 5-6)
- [ ] Auto-scaling AWS GPU
- [ ] Queue system completo
- [ ] Observabilidade (metrics, alerts)
- [ ] Security hardening
- [ ] Load testing

### Fase 4: Polish (Semanas 7-8)
- [ ] Multimodal router
- [ ] Advanced document parsing
- [ ] Education module
- [ ] Export engine
- [ ] Performance tuning

---

## 20. GLOSSÁRIO

| Termo | Definição |
|---|---|
| **TTFT** | Time To First Token — latência até o primeiro token da resposta |
| **SSE** | Server-Sent Events — protocolo streaming sobre HTTP |
| **vLLM** | Framework de serving LLM com PagedAttention (alto throughput) |
| **TGI** | Text Generation Inference — alternativa da HuggingFace |
| **RAG** | Retrieval Augmented Generation — busca + geração |
| **STT** | Speech-to-Text — reconhecimento de voz |
| **TTS** | Text-to-Speech — síntese de voz |
| **HMAC** | Hash-based Message Authentication Code — assinatura de requisições |

---

*Documento gerado para a arquitetura soberana VEREDA / SYNTEXA v3.0.*
