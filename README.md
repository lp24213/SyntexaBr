# Syntexa AI

Chat inteligente, multimídia e agentes IA — feito no Brasil.

## O que é

Syntexa é uma plataforma de IA completa: chat avançado, visão, voz e agentes autônomos. O site roda no Cloudflare Pages e a API no Railway + Azure.

- Site: https://syntexabr.com.br
- API: https://api.syntexabr.com.br

## Partes do projeto

- `frontend/` — site em Next.js (estático, hospedado no Cloudflare)
- `vereda_backend/` — API em Python/FastAPI (autenticação, pagamento, chat)
- `vereda_ai/` — núcleo de inteligência artificial
- `scripts/` — scripts de deploy e manutenção

## Rodar local

1. Copie `.env.example` pra `.env` e preencha suas chaves
2. Backend: `pip install -r requirements.txt && uvicorn vereda_backend.main:app`
3. Frontend: `cd frontend && npm install && npm run dev`

## Deploy

Deploy é feito via Railway (backend) e Cloudflare Pages (frontend). Sem máquina local rodando 24h.

## Contato

Problemas ou sugestões? Abre uma issue ou manda um email.
