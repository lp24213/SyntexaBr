# 🗺️ MAPA COMPLETO DO BACKEND - SYNTEXABR

**Data:** 2026-06-05  
**Projeto:** SyntexaBR - Sovereign Quantum AI Platform  
**Status:** Multi-tier Hybrid Architecture

---

## 📊 VISÃO GERAL

O backend do SyntexaBR é uma **arquitetura híbrida complexa** com:
- **FastAPI Python** como motor principal
- **Express.js Node.js** para filas e real-time
- **Módulos LLM especializados** (llm-core, llm-reasoning, llm-multimodal, etc)
- **Cloudflare Workers** para edge computing

---

## 🐍 PYTHON BACKEND (PRIMÁRIO)

### 1. `vereda_backend/` - O CORAÇÃO DA APLICAÇÃO

Este é o **backend principal** construído com FastAPI. Tudo passa por aqui.

#### 📌 Estrutura Principal:

```
vereda_backend/
├── main.py                          # Entry point (FastAPI app)
├── api/
│   ├── routes.py                    # Registrador de rotas (lazy loading)
│   ├── public.py                    # Chat público (sem autenticação)
│   ├── deps/                        # Dependências (auth, subscription)
│   └── v1/endpoints/                # TODAS as rotas da API
│       ├── auth.py                  # Login, JWT, signup
│       ├── chat.py                  # Chat principal
│       ├── health.py                # Health checks
│       ├── documents.py             # Gerenciar documentos
│       ├── export_api.py            # Exportar conversas (CSV, PDF, etc)
│       ├── subscription.py          # Gerenciar planos
│       ├── payments.py              # Processamento de pagamentos
│       ├── webhooks.py              # Webhooks gerais
│       ├── webhooks_billing.py      # Webhooks de billing
│       ├── admin.py                 # Endpoints admin
│       ├── agents.py                # Agentes autônomos
│       ├── autonomy.py              # Executores autônomos
│       ├── voice.py                 # API de voz
│       ├── vision.py                # API de visão
│       ├── multimodal_api.py        # Processamento multimodal
│       ├── media.py                 # Upload/processamento mídia
│       ├── files_api.py             # Gerenciar arquivos
│       ├── intel.py                 # Inteligência/análise
│       ├── research.py              # Research tools
│       ├── education.py             # Endpoints educacionais
│       ├── institutional.py         # Endpoints institucionais
│       ├── integrations.py          # Integrações (Zapier, etc)
│       ├── tools.py                 # Ferramentas (análise de imagem, math)
│       ├── feedback.py              # Feedback dos usuários
│       ├── desktop_downloads.py     # Downloads para app desktop
│       ├── modular_chat.py          # Chat modular
│       ├── execution.py             # Execução de tarefas
│       └── science.py               # Endpoints científicos
│
├── services/                        # LÓGICA DE NEGÓCIO (O motor!)
│   ├── chat_engine.py               # ⭐ MOTOR PRINCIPAL - Orquestra tudo
│   ├── ai_router.py                 # 🤖 Decide qual modelo usar
│   ├── agent_orchestrator_v2.py     # 🤖 Orquestra agentes
│   ├── autonomy_manager.py          # Gerencia autonomia
│   ├── autonomous_evolution.py      # Evolução de agentes
│   ├── conversation_store.py        # Armazenamento de conversas
│   ├── llm_client.py                # Cliente para chamadas LLM
│   ├── media_engine.py              # Processamento de mídia
│   ├── search_architecture.py       # Busca e RAG
│   ├── events.py                    # Orquestrador de eventos
│   ├── dashscope_image.py           # Integração com gerador de imagem
│   ├── tools.py                     # Ferramentas utilitárias
│   └── file_generators/             # Geradores (ODS, PDF, etc)
│
├── core/                            # CONFIGURAÇÃO E UTILIDADES
│   ├── config.py                    # ⚙️ Configurações gerais
│   ├── security.py                  # 🔐 JWT, autenticação
│   ├── security_config.py           # Políticas de segurança
│   ├── subscription.py              # 💳 Lógica de subscriptions
│   ├── chat_policy.py               # Política de chat
│   ├── syntexa_identity.py          # Identidade da IA
│   ├── syntexa_modes.py             # Modos de operação
│   ├── ai_proxy_client.py           # Proxy para IA
│   ├── answer_engine.py             # Motor de resposta
│   ├── context_budget.py            # Gestão de contexto
│   ├── rate_limit.py                # Rate limiting
│   ├── circuit_breaker.py           # Circuit breaker
│   ├── load_monitor.py              # Monitoramento de carga
│   ├── cache_redis.py               # Cache Redis
│   ├── redis_app.py                 # App Redis
│   ├── quantum_orchestrator.py      # Orquestrador quantum
│   ├── cognitive_layer.py           # Camada cognitiva
│   ├── vector_store_pg.py           # Vector embeddings PostgreSQL
│   ├── access_control.py            # Controle de acesso
│   ├── turnstile.py                 # Captcha Turnstile
│   ├── confidence_score.py          # Scoring
│   ├── llm_router_v2.py             # Router LLM
│   ├── text_polish.py               # Polimento de texto
│   ├── text_sanitize.py             # Sanitização
│   └── ... (20+ outros arquivos)
│
├── db/                              # DATABASE
│   ├── models.py                    # ⭐ Modelos SQLAlchemy
│   └── session.py                   # Session management
│
├── workers/                         # BACKGROUND WORKERS
│   ├── tasks.py                     # Celery tasks
│   ├── media_worker.py              # Worker de mídia
│   └── settings.py                  # Configurações
│
├── queues/                          # FILAS DE TRABALHO
│   └── media_jobs.py                # Gerenciador de jobs
│
├── autonomy/                        # SISTEMA AUTÔNOMO (Agentes)
│   ├── agents.py                    # Definição de agentes
│   ├── executor.py                  # Executor de tarefas
│   ├── tasks.py                     # Tarefas autônomas
│   ├── rag.py                       # Retrieval-Augmented Generation
│   ├── ingest.py                    # Ingestão de dados
│   ├── recovery.py                  # Recuperação de falhas
│   ├── crawler.py                   # Web crawler
│   └── healthcheck.py               # Health checks
│
├── middleware/                      # MIDDLEWARES
│   ├── rate_limit.py                # Rate limiting
│   └── subscription.py              # Subscription validation
│
├── cache/                           # CACHING
│   └── media_cache.py               # Cache de mídia
│
└── tests/                           # TESTES UNITÁRIOS
    ├── test_health_public.py
    ├── test_syntexa_identity_prompt.py
    ├── test_smart_export_unit.py
    ├── test_query_profile_unit.py
    ├── test_ods_generator.py
    └── ... (mais 7 testes)
```

---

### 2. `llm-*` Modules - PIPELINE DE IA ESPECIALIZADOS

Estes são **módulos Python** que são importados e usados por `vereda_backend`. NÃO são aplicações standalone.

#### 🧠 llm-core/ - Motor LLM Principal
Responsável pela execução base de modelos LLM
```
llm-core/
├── engine.py                 # Engine de execução
├── tokenizer.py              # Tokenização
├── router.py                 # Roteador de modelos
├── scheduler.py              # Scheduling de requisições
├── context.py                # Gerenciamento de contexto
├── prompt_optimizer.py       # Otimização de prompts
├── model_registry.py         # Registro de modelos disponíveis
├── memory_compressor.py      # Compressão de memória
├── kv_cache.py               # KV Cache para performance
├── streamer.py               # Streaming de respostas
└── batching.py               # Batching de requisições
```

#### 🤔 llm-reasoning/ - Raciocínio e Lógica
```
llm-reasoning/
├── reasoning_pipeline.py     # Pipeline completo
├── chain_of_thought.py       # Chain of Thought (passo a passo)
├── reflection.py             # Reflexão sobre respostas
├── verifier.py               # Verificação de respostas
├── planner.py                # Planejamento de ações
└── critic.py                 # Crítica de respostas
```

#### 👁️ llm-multimodal/ - Processamento Multimodal
```
llm-multimodal/
├── vision_engine.py          # Visão computacional
├── ocr_engine.py             # OCR (texto em imagens)
├── audio_engine.py           # Processamento de áudio
├── document_engine.py        # Processamento de docs
└── fusion_engine.py          # Fusão de modalidades
```

#### ⚛️ llm-quantum/ - Computação Quântica Híbrida
```
llm-quantum/
├── quantum_orchestrator.py   # Orquestra quantum computing
├── quantum_optimizer.py      # Otimizador quantum
├── quantum_scheduler.py      # Scheduler quantum
├── hybrid_quantum_runtime.py # Runtime híbrido
└── hybrid_router.py          # Router híbrido
```

#### 🔹 Outros Módulos
- **llm-kernel/** - Kernel neural core (bootstrap, neural execution)
- **llm-security/** - Guardrails de segurança
- **llm-inference/** - Engine de inferência
- **llm-router/** - Roteador de modelos
- **llm-runtime/** - Scheduler de runtime
- **llm-agents/** - Sistema de agentes
- **llm-autonomous/** - Sistemas autônomos
- **llm-context-engine/** - Engine de contexto
- **llm-embeddings/** - Embeddings/vetores
- **llm-memory/** - Gerenciamento de memória
- **llm-tokenizer/** - Tokenização avançada
- **llm-training/** - Treinamento de modelos
- **llm-vision/** - Visão especializada
- **llm-voice/** - Processamento de voz

---

## 🟢 NODEJS BACKEND

### `production-node/` - Express + BullMQ

```
production-node/
│
├── api/                      # Express.js API Server
│   ├── src/
│   │   ├── index.js          # Entry point (Express app)
│   │   ├── middleware/       # Express middlewares
│   │   ├── routes/           # API routes
│   │   ├── queue.js          # BullMQ configuration
│   │   ├── rateLimit.js      # Rate limiting
│   │   └── logger.js         # Pino logging
│   ├── package.json          # Dependencies
│   └── Dockerfile
│
├── queue-worker/             # BullMQ Background Worker
│   ├── src/
│   │   └── worker.js         # Worker logic
│   └── package.json
│
├── own-model-gateway/        # Gateway para modelos próprios
│   ├── server.js
│   └── package.json
│
└── worker-stt/               # Speech-to-Text Worker (placeholder)
```

**Dependencies Principais:**
- `bullmq` - Job queue system
- `express` - Web framework
- `socket.io` - Real-time communication
- `ioredis` - Redis client
- `pg` - PostgreSQL client
- `pino` - Logging

---

## 🏗️ INFRAESTRUTURA & GATEWAYS

### `infrastructure/`

```
infrastructure/
├── gateway-api/              # FastAPI Gateway (proxy público)
│   ├── main.py
│   ├── core/config.py
│   ├── core/ai_proxy.py
│   └── api/
│
├── local-private-ai/         # IA Local com Ollama
│   ├── main.py
│   ├── core/ollama_client.py
│   └── api/v1/endpoints/
│
├── ai-worker/                # Distributed AI Worker
│
├── local-hybrid/             # Hybrid Local Setup
│   ├── main.py
│   └── sync_agent.py
│
└── syntexa-native-worker/    # Native Syntexa Worker
    └── server.py
```

---

## ☁️ CLOUDFLARE WORKERS

```
cloudflare-workers/
├── src/
│   └── index.js              # Edge computing logic
├── wrangler.toml             # Configuration
└── package.json
```

**Responsabilidade:** CDN, caching, edge routing

---

## 🗄️ DATABASE & CACHE

### PostgreSQL (Primary)
```sql
-- Tabelas principais:
users              # Usuários da plataforma
conversations      # Histórico de chats
subscriptions      # Planos de usuário
payments           # Histórico de pagamentos
agents             # Configuração de agentes
documents          # Documentos uploaded
tokens             # Cache de tokens JWT
vector_store       # Embeddings para RAG
```

**Localização:** `vereda_backend/db/models.py`

### Redis (Cache & Pub/Sub)
- Cache de respostas
- Job queue (BullMQ)
- Session storage
- Real-time notifications (Socket.IO)

---

## ⚙️ CONFIGURAÇÕES

### Python
```
pyproject.toml           # Project metadata + dependencies
requirements.txt         # Python packages
requirements.railway.txt # Railway-specific packages
```

### Node.js
```
cloudflare-workers/package.json
production-node/api/package.json
production-node/queue-worker/package.json
```

### Deployment
```
.env                     # Environment variables
docker-compose.yml       # Main stack
docker-compose.own-model.yml      # Com modelo próprio
docker-compose.redis.yml          # Redis standalone
Dockerfile               # Docker image
Dockerfile.railway       # Railway-specific
railway.json/toml        # Railway config
wrangler.toml           # Cloudflare config
```

---

## 🔄 FLUXO DE DADOS

```
┌─────────────────────────────────────────────────────────┐
│                    CLIENTE/BROWSER                       │
└────────────────────────┬────────────────────────────────┘
                         │
                         ↓
        ┌────────────────────────────────┐
        │   Cloudflare Workers (Edge)    │
        │   - Caching                    │
        │   - Rate limiting              │
        │   - Routing                    │
        └────────────┬───────────────────┘
                     │
        ┌────────────▼────────────┐
        │ Express.js (Node.js)    │ ◄─── WebSocket (Socket.IO)
        │ - Real-time             │
        │ - Job submission         │
        │ - Streaming             │
        └────────────┬───────────┘
                     │
        ┌────────────▼──────────────────────┐
        │  FastAPI (vereda_backend)         │
        │  ├─ routes (30+ endpoints)        │
        │  ├─ services (chat, agents)       │
        │  └─ core (auth, config, cache)    │
        │                                   │
        │  ├─ AI processing:                │
        │  │  ├─ llm-core                   │
        │  │  ├─ llm-reasoning              │
        │  │  ├─ llm-multimodal             │
        │  │  └─ llm-quantum                │
        │  │                                │
        │  └─ Background:                   │
        │     ├─ autonomy/ (agents)         │
        │     └─ workers/ (Celery tasks)    │
        └────────────┬──────────────────────┘
                     │
        ┌────────────▼──────────────────┐
        │  BullMQ Job Queue (Redis)     │
        │  - Media processing           │
        │  - Async tasks                │
        └────────────┬──────────────────┘
                     │
        ┌────────────▼──────────────────┐
        │  Node.js Queue Worker         │
        │  - Processes jobs             │
        │  - Updates database           │
        └────────────┬──────────────────┘
                     │
        ┌────────────▼──────────────────┐
        │  PostgreSQL Database          │
        │  + Redis Cache                │
        │  + Vector Store (Embeddings)  │
        └───────────────────────────────┘
```

---

## 🎯 FLUXO DE UM CHAT REQUEST

```
1. Cliente envia: POST /v1/chat
   
2. Cloudflare Workers
   └─→ Rate limit check
   └─→ Rota para Express ou FastAPI
   
3. FastAPI (vereda_backend)
   └─→ Endpoint: chat.py
   └─→ Valida JWT (security.py)
   └─→ Checa subscription
   └─→ Chama: chat_engine.py
   
4. chat_engine.py (motor principal)
   └─→ Recupera contexto da conversa
   └─→ Chama: ai_router.py
   
5. ai_router.py (rooteador de modelo)
   └─→ Decide qual modelo usar
   └─→ Pode usar: GPT, Claude, modelo local, etc
   
6. llm-core (processamento)
   └─→ Tokenização (llm-core/tokenizer.py)
   └─→ Routing (llm-core/router.py)
   └─→ Batching se necessário (llm-core/batching.py)
   
7. Raciocínio (se necessário)
   └─→ llm-reasoning/chain_of_thought.py
   └─→ llm-reasoning/reasoning_pipeline.py
   
8. Multimodal (se imagem/áudio)
   └─→ llm-multimodal/vision_engine.py
   └─→ llm-multimodal/audio_engine.py
   
9. Resposta
   └─→ Salva na DB
   └─→ Envia via Socket.IO (real-time)
   └─→ Cache em Redis
   
10. Background jobs (se necessário)
    └─→ Submete para BullMQ queue
    └─→ Node.js worker processa
    └─→ Notifica cliente
```

---

## ⚠️ DUPLICAÇÕES IDENTIFICADAS

### 🔴 CRÍTICAS

1. **Endpoints de Chat Duplicados**
   - FastAPI tem: `api/v1/endpoints/chat.py`
   - Express tem: `src/routes/` chat routes
   - **Problema:** Qual é a fonte de verdade?

2. **Router de IA Duplicado**
   - `vereda_backend/core/ai_router.py`
   - `llm-router/router.py`
   - **Problema:** Ambos decidem qual modelo usar

3. **Autenticação em Múltiplos Lugares**
   - FastAPI: `vereda_backend/core/security.py`
   - Express: pode ter sua própria
   - Cloudflare: pode validar JWT
   - **Problema:** Sem sincronização = vulnerabilidades

### 🟡 IMPORTANTES

4. **Rate Limiting**
   - FastAPI: `middleware/rate_limit.py`
   - Express: `src/rateLimit.js`
   - Cloudflare: pode ter seu próprio

5. **Configuração**
   - `vereda_backend/core/config.py`
   - `.env` files espalhados
   - `railway.json`
   - `wrangler.toml`

---

## ✅ RECOMENDAÇÕES DE CONSOLIDAÇÃO

### Imediato (MVP)
1. **Definir responsabilidades claras:**
   - FastAPI = Chat + IA + Lógica principal
   - Express = Queues + Real-time APENAS
   - Cloudflare = Proxy + Cache

2. **Consolidar autenticação:**
   - Usar JWT gerado por FastAPI
   - Express valida (não gera novo)
   - Cloudflare valida token

3. **Router de IA:**
   - Centralizar em `llm-router/` ou `vereda_backend/core/ai_router.py`
   - Remover duplicação

### Médio Prazo
4. **Unificar endpoints:**
   - Remover chat routes do Express
   - Express apenas recebe comandos via Pub/Sub

5. **Config centralizada:**
   - Service de config que todos consultam
   - Uma fonte de verdade

### Longo Prazo
6. **Considerar:**
   - GraphQL para API unificada?
   - gRPC para comunicação interna?
   - Separar em microserviços por domínio?

---

## 🔗 DEPENDÊNCIAS PRINCIPAIS

```python
# Python (vereda_backend)
fastapi==0.115.0
sqlalchemy              # ORM
pydantic               # Validation
redis                  # Cache
celery                 # Task queue
torch>=2.1.0          # ML
transformers>=4.36.0  # LLMs
llama-cpp-python      # Local models
```

```javascript
// Node.js (production-node/api)
bullmq@^5.12.12       // Job queue
express@^4.21.2       // Web framework
socket.io@^4.8.0      // Real-time
ioredis@^5.4.1        // Redis
pg@^8.15.0            // PostgreSQL
```

---

## 🗂️ ARQUIVOS IMPORTANTES NO ROOT

```
root/
├── BACKEND_COMPLETE_MAP.json       # Este mapa (JSON)
├── BACKEND_COMPLETE_MAP.md         # Este mapa (Markdown) ← VOCÊ ESTÁ AQUI
├── vereda_backend/                 # ⭐ Main backend
├── production-node/                # Express + BullMQ
├── llm-*/                           # LLM modules
├── infrastructure/                 # Gateways e workers
├── cloudflare-workers/             # Edge computing
├── docker-compose.yml              # Stack principal
├── Dockerfile                      # Image principal
├── pyproject.toml                  # Python project config
├── requirements.txt                # Python deps
└── .env                            # Environment config
```

---

## 📋 QUICK REFERENCE

| Preciso... | Edito... |
|-----------|----------|
| Adicionar endpoint | `vereda_backend/api/v1/endpoints/*.py` |
| Adicionar serviço | `vereda_backend/services/*.py` |
| Mudar lógica de chat | `vereda_backend/services/chat_engine.py` |
| Mudar modelo IA | `vereda_backend/core/ai_router.py` |
| Adicionar autenticação | `vereda_backend/core/security.py` |
| Background job | `vereda_backend/workers/tasks.py` + BullMQ |
| Real-time | Express + Socket.IO |
| Cache | `vereda_backend/core/cache_redis.py` |
| Database | `vereda_backend/db/models.py` |
| Configuração | `vereda_backend/core/config.py` |
| Segurança | `vereda_backend/core/security*.py` |
| Rate limit | `vereda_backend/middleware/rate_limit.py` |
| Agentes IA | `vereda_backend/autonomy/agents.py` |

---

**Gerado em:** 2026-06-05  
**Versão:** 1.0  
**Status:** Pronto para consolidação
