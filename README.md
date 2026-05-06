# Syntexa Ultra AI Platform

Plataforma de IA **Syntexa**, com arquitetura modular para chat avançado, motores científicos, agentes, visão e multimídia.

## Arquitetura (produção primeiro)

| Camada | Onde roda |
|--------|-----------|
| Frontend estático | **Cloudflare Pages** — `https://syntexabr.com.br` |
| API HTTP (FastAPI) | **VM Azure** — `https://api.syntexabr.com.br` (uvicorn + nginx) |
| Ollama / LLM | **Mesma VM** (`llm-server`/Docker) ou **Azure OpenAI** / TGI (via `.env`) |
| Redis / fila ARQ | **Redis gerenciado ou VM** — `REDIS_URL` no servidor (recomendado para filas e cache em escala) |

**Escala (milhares de utilizadores):** o limite real é **inferência** (GPU/RAM) e **base de dados**. Para tráfego massivo: `REDIS_URL` obrigatório, PostgreSQL em vez de SQLite, várias réplicas da API atrás de um balanceador, e modelo servido por **Azure OpenAI** ou **pool Ollama** dedicado — não uma única VM indefinidamente.

A máquina do desenvolvedor é só para **código** e **deploy** (`.\deploy-syntexa.ps1 deploy`). Modelos e dados de produção ficam no servidor.

## Estrutura

- `vereda_backend/`: API HTTP (FastAPI), rotas públicas/admin.
- `vereda_ai/`: núcleo de IA.
- `frontend/`: app Next (export estático); build e publicação via Cloudflare.
- `scripts/`: deploy, nginx, PM2 (`ecosystem.config.cjs`), systemd (`syntexa.service.example`).
- `requirements.txt`: dependências Python.

## Deploy

- **Completo (Cloudflare + VM):** `.\deploy-syntexa.ps1 deploy`
- **Só API:** `.\deploy-syntexa.ps1 deploy-back`
- **Só frontend:** `.\deploy-syntexa.ps1 deploy-front` (requer `npm`/`wrangler` para build e upload)

Processo no servidor: **systemd** é o caminho suportado pelo deploy — unidade `scripts/syntexa-backend.service` (instalada em `/etc/systemd/system/syntexa-backend.service`, `Restart=always`).  
Se a API cair: `.\deploy-syntexa.ps1 repair-api` (SSH) ou no servidor `bash /opt/syntexa/scripts/ensure_api_stack.sh`. HTTPS/nginx: `.\deploy-syntexa.ps1 fix-proxy`.

## Endpoints principais (produção)

Base: `https://api.syntexabr.com.br`

- `GET /health` — status do serviço.
- `POST /v1/chat/completions` — chat compatível com OpenAI.
- Demais rotas conforme OpenAPI exposta em produção.

## Variáveis de ambiente

Ver `.env.example` (valores de exemplo para o **servidor**; não commitar `.env` com segredos).
