# syntax=docker/dockerfile:1
# Syntexa AI Worker — Kaggle / GPU / Servidor externo (IA pesada)
FROM python:3.12-slim-bookworm
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       gcc libpq-dev curl libgomp1 ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY infrastructure/ai-worker/requirements.txt ./requirements-ai.txt
RUN pip install --no-cache-dir -r requirements-ai.txt

COPY infrastructure/shared ./infrastructure/shared
COPY infrastructure/ai-worker ./worker

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV UVICORN_WORKERS=1

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8001/health || exit 1

ENTRYPOINT ["python", "-m", "uvicorn", "worker.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]
