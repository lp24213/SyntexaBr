#!/usr/bin/env bash
# backend-restart: pip + systemctl + espera /health
set -e
cd /opt/syntexa
# shellcheck source=/dev/null
source .venv/bin/activate
pip install -q -U pip
pip install -q -r requirements.txt
export PYTHONPATH=/opt/syntexa
systemctl restart syntexa-backend
echo "Aguardando uvicorn abrir a porta (ate 20s)..."
n=0
while [ "$n" -lt 20 ]; do
  if curl -sf --connect-timeout 3 https://api.syntexabr.com.br/health >/dev/null 2>&1; then
    echo "[OK] /health (público)"
    curl -sS https://api.syntexabr.com.br/health
    echo ""
    systemctl status syntexa-backend --no-pager -l | head -n 18
    exit 0
  fi
  n=$((n+1))
  sleep 1
done
echo "[ERRO] Timeout — uvicorn nao respondeu. Journal:"
journalctl -u syntexa-backend -n 50 --no-pager
exit 1
