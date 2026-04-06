#!/usr/bin/env bash
# Reinício remoto (comando restart do deploy-syntexa.ps1)
set -e
cd /opt/syntexa
if [ -f /etc/systemd/system/syntexa-backend.service ]; then
  systemctl restart syntexa-backend
  sleep 5
  curl -sfS --connect-timeout 5 http://127.0.0.1:8000/health && echo "" || journalctl -u syntexa-backend -n 40 --no-pager
else
  echo "Sem unit systemd; rode deploy-back para instalar syntexa-backend.service"
  exit 1
fi
if curl -sf --connect-timeout 12 https://api.syntexabr.com.br/health > /dev/null; then
  echo "[OK] API HTTPS publica"
else
  echo "[AVISO] HTTPS publico falhou — nginx/DNS? tente: fix-proxy"
fi
