# Syntexa Ultra AI Platform

Plataforma de IA **Syntexa**, com arquitetura modular para:

- chat avançado estilo OpenAI
- motores científicos (math/física/engenharia)
- agentes autônomos
- visão computacional
- geração multimídia (imagem/vídeo/música – stubs preparados)
- memória vetorial e RAG

## Estrutura

- `vereda_backend/`: API HTTP (FastAPI), autenticação, rotas públicas/admin (pacote interno da Syntexa).
- `vereda_ai/`: núcleo de IA (core, ai, agents, memory, science, tools, vision, media, execution, database) da Syntexa.
- `frontend/`: playground web de chat/admin.
- `requirements.txt`: dependências Python.

## Como rodar o backend

```bash
pip install -r requirements.txt
uvicorn vereda_backend.main:app --reload
```

Servidor padrão: `http://127.0.0.1:8000`.

## Endpoints principais (até agora)

- `GET /health` – status do serviço.
- `POST /v1/chat/completions` – chat compatível com OpenAI (com users/admin).
- `POST /v1/tools/math` – avaliação de expressões matemáticas.
- `POST /v1/tools/sql` – consultas SELECT seguras (admin).
- `POST /v1/tools/image/analyze` – análise básica de imagem.
- `POST /v1/media/images/generate` – stub de geração de imagem.
- `POST /v1/media/videos/analyze` – stub de análise de vídeo.
- `POST /v1/media/videos/generate` – stub de geração de vídeo.
- `POST /v1/media/music/generate` – stub de geração de música.

