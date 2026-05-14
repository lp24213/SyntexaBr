#!/bin/sh
set -e
# Produção: workers só com PostgreSQL (vários processos); SQLite = 1 worker.
WORKERS="${UVICORN_WORKERS:-2}"
TO="${UVICORN_TIMEOUT_KEEPALIVE:-120}"
DBURL="${DATABASE_URL:-}"
case "$DBURL" in
  sqlite*|"") WORKERS=1 ;;
esac
PORT="${PORT:-8000}"
exec python -m uvicorn vereda_backend.main:app \
  --host 0.0.0.0 --port "$PORT" \
  --workers "$WORKERS" \
  --timeout-keep-alive "$TO" \
  --proxy-headers \
  --forwarded-allow-ips '*'
