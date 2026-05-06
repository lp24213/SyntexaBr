#!/usr/bin/env bash
# Produção: keep-alive longo; uvloop vem do uvicorn[standard] quando disponível.
# UVICORN_WORKERS>1 só com PostgreSQL (evitar SQLite com vários processos).
# USE_GUNICORN=1: gunicorn + UvicornWorker (mesmo app ASGI; útil com timeouts finos no master).
set -euo pipefail
ROOT="/opt/syntexa"
cd "$ROOT"
export PYTHONPATH="$ROOT"
export PYTHONDONTWRITEBYTECODE=1
TO="${UVICORN_TIMEOUT_KEEPALIVE:-120}"
W="${UVICORN_WORKERS:-1}"
USE_GUNICORN="${USE_GUNICORN:-0}"

if [ "$USE_GUNICORN" = "1" ]; then
  exec "$ROOT/.venv/bin/gunicorn" vereda_backend.main:app \
    -k uvicorn.workers.UvicornWorker \
    -b 0.0.0.0:8000 \
    --workers "$W" \
    --timeout "$TO" \
    --graceful-timeout 30 \
    --keep-alive 5 \
    --forwarded-allow-ips='*'
elif [ "$W" -gt 1 ] 2>/dev/null; then
  exec "$ROOT/.venv/bin/python" -m uvicorn vereda_backend.main:app \
    --host 0.0.0.0 --port 8000 \
    --workers "$W" \
    --timeout-keep-alive "$TO" \
    --proxy-headers \
    --forwarded-allow-ips '*'
else
  exec "$ROOT/.venv/bin/python" -m uvicorn vereda_backend.main:app \
    --host 0.0.0.0 --port 8000 \
    --timeout-keep-alive "$TO" \
    --proxy-headers \
    --forwarded-allow-ips '*'
fi
