#!/usr/bin/env bash
# Rode no Hetzner como root (após deploy ou se a API cair):
#   bash /opt/syntexa/scripts/ensure_api_stack.sh
set -euo pipefail
ROOT="${ROOT:-/opt/syntexa}"
cd "$ROOT"

echo "=== [0] carregar .env (REDIS_URL, etc.) ==="
if [[ -f "$ROOT/.env" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "$ROOT/.env" 2>/dev/null || true
  set +a
fi

echo "=== [1] systemd: syntexa-backend ==="
if [[ ! -f "$ROOT/scripts/syntexa-backend.service" ]]; then
  echo "ERRO: falta $ROOT/scripts/syntexa-backend.service — faça deploy-back primeiro."
  exit 1
fi
install -m 644 "$ROOT/scripts/syntexa-backend.service" /etc/systemd/system/syntexa-backend.service
systemctl daemon-reload
systemctl enable syntexa-backend
command -v pm2 >/dev/null 2>&1 && pm2 delete syntexa-backend 2>/dev/null || true
pkill -9 -f 'uvicorn vereda_backend.main:app' 2>/dev/null || true
sleep 2
systemctl restart syntexa-backend
sleep 3
systemctl --no-pager -l status syntexa-backend || true

echo "=== [1b] worker ARQ (opcional; exige REDIS_URL) ==="
if [[ -n "${REDIS_URL:-}" ]] && [[ -f "$ROOT/scripts/syntexa-worker.service" ]]; then
  install -m 644 "$ROOT/scripts/syntexa-worker.service" /etc/systemd/system/syntexa-worker.service
  systemctl daemon-reload
  systemctl enable syntexa-worker 2>/dev/null || true
  systemctl restart syntexa-worker 2>/dev/null || true
  sleep 2
  systemctl --no-pager -l status syntexa-worker --lines=10 || true
else
  echo "  (sem worker: defina REDIS_URL e inclua syntexa-worker.service no deploy)"
fi

echo "=== [2] nginx (443 -> uvicorn) ==="
systemctl enable nginx 2>/dev/null || true
systemctl start nginx 2>/dev/null || true
systemctl --no-pager -l status nginx --lines=5 || true

echo "=== [3] firewall (se ufw ativo) ==="
if command -v ufw >/dev/null 2>&1 && ufw status 2>/dev/null | grep -q 'Status: active'; then
  ufw allow 80/tcp comment 'http' 2>/dev/null || ufw allow 80/tcp
  ufw allow 443/tcp comment 'https' 2>/dev/null || ufw allow 443/tcp
  echo "Regras 80/443 garantidas."
fi

echo "=== [4] portas em escuta ==="
ss -tlnp 2>/dev/null | grep -E ':8000|:443|:80' || true

echo "=== [5] health local (uvicorn) ==="
curl -sfS --connect-timeout 3 "http://127.0.0.1:8000/health" && echo "" || echo "FALHA: uvicorn não responde na 8000 — journalctl -u syntexa-backend -n 80"

API_HOST="api.syntexabr.com.br"
echo "=== [6] HTTPS neste host (nginx + TLS, sem depender de DNS global) ==="
if curl -sfS --connect-timeout 10 --resolve "${API_HOST}:443:127.0.0.1" "https://${API_HOST}/health" 2>/dev/null; then
  echo ""
elif curl -sfS --connect-timeout 10 "https://${API_HOST}/health" 2>/dev/null; then
  echo ""
else
  echo "INFO: TLS/DNS global ainda nao OK neste teste — rode: bash $ROOT/scripts/setup_nginx_api.sh"
fi

echo "=== fim ==="
