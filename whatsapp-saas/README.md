# 🚀 Syntexa WhatsApp SaaS Backend

Plataforma empresarial de chatbot WhatsApp integrada com LLM Syntexa. Multi-tenant, escalável, pronta para monetização.

## 📋 Stack Técnico

- **Runtime**: Node.js 20+ / TypeScript
- **Framework**: Fastify (ultra-rápido)
- **Database**: PostgreSQL com pgvector
- **Cache/Queue**: Redis (Streams)
- **Edge**: Cloudflare Workers (gateway)
- **LLM**: Syntexa (interno) + OpenAI (fallback)
- **API Externa**: Meta WhatsApp Cloud API v23.0

## 🏗️ Arquitetura

```
Meta WhatsApp Cloud API
         ↓
Cloudflare Worker (whatsapp-gateway)
  ├─ Validação HMAC SHA256
  ├─ Rate Limiting Edge
  └─ Proxy → Backend
         ↓
Fastify Backend (Port 3001)
  ├─ /webhook/whatsapp → Redis Queue
  ├─ /messages → CRUD
  ├─ /companies → Multi-tenant
  └─ /tools → PDF, Excel, etc
         ↓
Async Queue Processing
  ├─ Recuperar contexto (memory_vectors)
  ├─ Chamar Syntexa LLM
  ├─ Parse tool requests
  └─ Enviar resposta via WhatsApp
```

## ✅ Completado

- ✅ Schema PostgreSQL (8 tabelas)
- ✅ Servidor Fastify com segurança
- ✅ Rota webhook com validação HMAC
- ✅ Orchestrador de mensagens
- ✅ Rotas REST (messages, companies, config, tools, memory)
- ✅ Cloudflare Worker gateway
- ✅ Logging centralizado (Winston)

## 🔧 Setup & Deployment

### 1. Preparar Ambiente

```bash
cd whatsapp-saas

# Copiar env template
cp .env.example .env

# Editar com suas credenciais Meta
# Obter em: https://developers.facebook.com/apps
nano .env
```

### 2. Dependências

```bash
npm install
```

### 3. Migrations Database

```bash
# Aplicar schema
psql -U postgres -d syntexa -f ../migrations/whatsapp_saas_001_initial.sql

# Verificar
psql -U postgres -d syntexa -c "\dt whatsapp.*"
```

### 4. Desenvolvimento Local

```bash
# Terminal 1: Backend
npm run dev
# Saída: Server running on http://localhost:3001

# Terminal 2: Test webhook
curl -X GET "http://localhost:3001/webhook/whatsapp?hub_verify_token=staging-verify-token&hub_challenge=test123"
```

### 5. Build & Production

```bash
# Build TypeScript
npm run build

# Start servidor
npm start

# Deploy Cloudflare Worker
cd cloudflare
wrangler deploy --env production
```

## 🔐 Configurar Meta Webhooks

### 1. Criar App Meta

- Ir: https://developers.facebook.com/apps
- Criar novo app → "Business"
- Nomear: "Syntexa WhatsApp SaaS"

### 2. Adicionar WhatsApp Product

- Dentro do app, adicionar "WhatsApp" product
- Obter:
  - `WHATSAPP_BUSINESS_ACCOUNT_ID`
  - `WHATSAPP_PHONE_NUMBER_ID`
  - `WHATSAPP_ACCESS_TOKEN`

### 3. Configurar Webhook

- Em app settings:
  - **Webhook URL**: `https://whatsapp.syntexabr.com.br/webhook/whatsapp`
  - **Verify Token**: (gere um token aleatório seguro)
  - **App Secret**: (copie e guarde em segredo)

- Em Webhook Fields, inscrever-se em:
  - ✅ `messages`
  - ✅ `message_template_status_update`
  - ✅ `message_template_quality_update`

### 4. Variáveis de Ambiente

```bash
export WHATSAPP_VERIFY_TOKEN="seu-token-seguro-aqui"
export WHATSAPP_APP_SECRET="app-secret-da-meta"
export WHATSAPP_ACCESS_TOKEN="access-token-da-meta"
```

## 📡 API Endpoints

### Health & Monitoring

```bash
GET /health
# Resposta: { status: "ok", database: "connected", version: "1.0.0" }
```

### Webhooks

```bash
# Validação (Meta)
GET /webhook/whatsapp?hub_verify_token=XXX&hub_challenge=XXX

# Eventos (Meta → nosso backend)
POST /webhook/whatsapp
Headers: X-Hub-Signature-256: sha256=...
Body: { entry: [{ changes: [{ field: "messages", value: { ... } }] }] }
```

### Mensagens

```bash
# Listar conversa
GET /messages/:conversationId

# Enviar manualmente
POST /messages
Body: { conversationId: "...", content: "..." }
```

### Empresas

```bash
# Listar todas
GET /companies

# Criar nova
POST /companies
Body: { name: "Acme Corp", email: "contact@acme.com", plan: "pro" }

# Adicionar número
POST /companies/:id/phone-numbers
Body: { phone_number_id: "...", display_number: "11987654321", access_token: "..." }
```

### Configuração

```bash
# Obter config empresa
GET /config/:companyId

# Atualizar config
PUT /config/:companyId
Body: { system_prompt: "Você é um vendedor...", max_tokens_per_message: 1000 }
```

### Tools (Exportação)

```bash
# Gerar PDF
POST /tools/pdf
Body: { conversationId: "...", title: "Relatório", sections: [...] }
Response: application/pdf

# Gerar Excel
POST /tools/xlsx
Body: { conversationId: "...", title: "Dados", rows: [...], header: [...] }
Response: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
```

### Memória

```bash
# Listar memórias
GET /memory/:conversationId

# Sumário conversa
GET /memory/summary/:conversationId

# Adicionar à memória
POST /memory/:conversationId
Body: { content: "Cliente trabalha na área de TI" }
```

## 🎯 Fluxo Completo de Mensagem

1. **Receber**: Meta envia POST para `/webhook/whatsapp`
2. **Validar**: HMAC SHA256 da assinatura
3. **Enqueue**: Adicionar à fila Redis (`queue:messages`)
4. **Processar**:
   - Recuperar histórico da conversa (últimas 10 msgs)
   - Buscar memória vetorizada (pgvector similarity)
   - Montar prompt com contexto
   - Chamar Syntexa LLM (`/v1/chat/completions`)
5. **Parsear**: Resposta contém text/tool_call?
6. **Executar**: Se houver tool_call (pdf, xlsx, etc):
   - Chamar API de exportação
   - Upload do arquivo para WhatsApp Media Storage
7. **Responder**: Enviar via Meta Graph API
8. **Armazenar**: Guardar em `whatsapp.messages` com tokens_used

## 💰 Monetização (Ready)

Schema suporta:

- **Planos**: free, pro, enterprise
- **Token Limits**: `companies.tokens_limit`
- **Token Usage**: `companies.tokens_used` + `messages.tokens_used`
- **Billing**: Integração Stripe ready (webhooks, invoices)

### Tiers Exemplo

| Plan | Msgs/mês | Tools | Preço |
|------|----------|-------|-------|
| Free | 1000 | PDF | $0 |
| Pro | 50k | PDF, Excel, DOCX | $99 |
| Enterprise | Unlimited | Todos + API | Custom |

## 🚨 Security

- ✅ HMAC SHA256 webhook validation
- ✅ JWT authentication
- ✅ CORS allowlist
- ✅ Helmet headers
- ✅ Rate limiting (1000/min/IP)
- ✅ PostgreSQL parameterized queries
- ✅ Secrets via .env (nunca comitar)

## 📊 Monitoring

```bash
# Logs
tail -f logs/combined.log

# Fila Redis
redis-cli LRANGE queue:messages 0 -1

# DB connections
psql -c "SELECT datname, count(*) FROM pg_stat_activity GROUP BY datname"

# OpenTelemetry (Datadog/Sentry)
# Ativar em .env: SENTRY_DSN, DATADOG_API_KEY
```

## 🐛 Troubleshooting

### Webhook não recebendo eventos

1. Validar HMAC:
```bash
# Meta envia assinatura em: X-Hub-Signature-256
# Format: sha256=XXXX
# Calcular: HMAC-SHA256(body, app_secret)
```

2. Verificar token:
```bash
# GET /webhook/whatsapp?hub_verify_token=XXX&hub_challenge=YYY
# Deve retornar: YYY
```

### LLM respondendo muito lentamente

- Aumentar pool PostgreSQL: `max: 20` → `max: 50`
- Usar OpenAI fallback (mais rápido) em case de timeout
- Implementar caching de responses

### Redis queue crescendo

- Verificar se worker está processando: `LLEN queue:messages`
- Reiniciar worker: `npm stop && npm start`
- Limpar se necessário: `redis-cli DEL queue:messages`

## 📚 Recursos Úteis

- [Meta WhatsApp Cloud API Docs](https://developers.facebook.com/docs/whatsapp/cloud-api/reference)
- [Fastify Docs](https://www.fastify.io/)
- [pgvector Docs](https://github.com/pgvector/pgvector)
- [Cloudflare Workers Docs](https://developers.cloudflare.com/workers/)

## 🤝 Contribuindo

1. Criar branch: `git checkout -b feature/sua-feature`
2. Commit: `git commit -m "feat: descrição"`
3. Push: `git push origin feature/sua-feature`
4. PR para `main`

## 📜 Licença

Syntexa © 2024 - Propriedade intelectual reservada.

---

**Status**: 🟢 Pronto para MVP
**Última atualização**: 2024-01-15
**Mantido por**: Equipe Syntexa
