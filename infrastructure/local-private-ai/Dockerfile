# syntax=docker/dockerfile:1
# Syntexa Local Private AI — Ollama / Servidor local com GPU
FROM python:3.12-slim-bookworm
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc curl \
    && rm -rf /var/lib/apt/lists/*

COPY infrastructure/local-private-ai/requirements.txt ./requirements-local.txt
RUN pip install --no-cache-dir -r requirements-local.txt

COPY infrastructure/local-private-ai ./local_private_ai

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8002

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8002/health || exit 1

ENTRYPOINT ["python", "-m", "uvicorn", "local_private_ai.main:app", "--host", "0.0.0.0", "--port", "8002", "--workers", "1"]
