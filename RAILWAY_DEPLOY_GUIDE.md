# Syntexa Backend — Deploy no Railway (Passo a Passo)

## O PROBLEMA
O projeto atual s tem:
- PostgreSQL (banco)
- Redis (cache)
- todo-list (funo Bun — NO o backend)

FALTA: Um servio WEB para rodar o FastAPI Python.

---

## PASSO 1: Criar Servio Web no Railway Dashboard

1. Acesse: https://railway.com/project/2d58ba02-7029-46d8-bee0-ee31caf09c4c
2. Clique no boto **"New"** (canto superior direito)
3. Selecione **"Empty Service"** ou **"Deploy from GitHub repo"**
4. Nomeie: **"syntexa-backend"**
5. Se escolheu GitHub: selecione o repo `luisp/SyntexaBr`
6. Clique em **"Deploy"**

---

## PASSO 2: Configurar Variveis de Ambiente

No dashboard do servio "syntexa-backend", v em "Variables" e adicione:

```
VEREDA_SECRET_KEY=syntexa-sovereign-key-2026-secure-change-me
VEREDA_ADMIN_EMAIL=admin@syntexabr.com.br
VEREDA_ADMIN_PASSWORD=SyntexaAdmin2026Secure!
DATABASE_URL=${{Postgres.DATABASE_URL}}  (ou copie do servio Postgres)
REDIS_URL=${{Redis.REDIS_URL}}  (ou copie do servio Redis)
DEFAULT_LLM=syntexa_native
API_V1_PREFIX=/v1
FRONTEND_ORIGIN=https://syntexabr.com.br
FRONTEND_BASE_URL=https://syntexabr.com.br
API_PUBLIC_BASE_URL=https://api.syntexabr.com.br
AUTONOMY_EVOLUTION_LOOP_ENABLED=true
CHAT_STRICT_REAL_PROVIDERS=false
UVICORN_WORKERS=2
UVICORN_TIMEOUT_KEEPALIVE=120
PYTHONUNBUFFERED=1
ENVIRONMENT=production
```

---

## PASSO 3: Configurar Domnio

No servio "syntexa-backend", v em "Settings" > "Domains":
- Clique em "Generate Domain" ou use custom: `api.syntexabr.com.br`

---

## PASSO 4: Deploy Automtico

O Railway vai detectar o `railway.toml` na raiz do repo e fazer deploy automaticamente.

Ou faa manualmente pelo dashboard clicando em "Deploy".

---

## PASSO 5: Cloudflare Workers Gateway

Aps o backend estar online, configure o Cloudflare Workers:

1. Acesse o dashboard Cloudflare: https://dash.cloudflare.com
2. V em "Workers & Pages"
3. Crie um novo Worker: "syntexa-gateway"
4. Cole o cdigo do arquivo `cloudflare-workers/src/index.js`
5. Atualize a varivel `RAILWAY_BACKEND_URL` com o URL real do Railway
6. Configure as rotas customizadas para `api.syntexabr.com.br`

---

## STATUS ATUAL
- PostgreSQL: ONLINE
- Redis: ONLINE
- Backend Python: PENDENTE (falta criar servio web)
- Cloudflare Gateway: PENDENTE

## PRXIMO PASSO
**Crie o servio web "syntexa-backend" no dashboard do Railway AGORA.**
