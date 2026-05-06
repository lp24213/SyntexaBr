#!/usr/bin/env bash
# Prometheus text do backend (rota raiz /metrics).
set -euo pipefail
BASE="${1:-http://127.0.0.1:8000}"
curl -fsS "${BASE%/}/metrics" | head -n 200
echo "..."
echo "[scrape] total lines (approx): $(curl -fsS "${BASE%/}/metrics" | wc -l)"
