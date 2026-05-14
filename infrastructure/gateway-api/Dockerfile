# syntax=docker/dockerfile:1
# Syntexa Gateway API — Railway (leve, sem IA)
FROM python:3.12-slim-bookworm
WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY infrastructure/gateway-api/requirements.txt ./requirements-gateway.txt
RUN pip install --no-cache-dir -r requirements-gateway.txt

COPY infrastructure/shared ./infrastructure/shared
COPY vereda_backend/core/config.py ./vereda_backend/core/config.py
COPY vereda_backend/core/security.py ./vereda_backend/core/security.py
COPY vereda_backend/core/public_messages.py ./vereda_backend/core/public_messages.py
COPY vereda_backend/db ./vereda_backend/db
COPY vereda_backend/schemas ./vereda_backend/schemas
COPY infrastructure/gateway-api ./gateway

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV UVICORN_WORKERS=2

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=2 \
  CMD curl -fsS http://127.0.0.1:8000/health || exit 1

ENTRYPOINT ["python", "-m", "uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--proxy-headers", "--forwarded-allow-ips", "*"]
