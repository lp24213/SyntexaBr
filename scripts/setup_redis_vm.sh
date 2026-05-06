#!/usr/bin/env bash
# Redis local na VM (Ubuntu): só escuta em 127.0.0.1 por defeito — não expõe fila à internet.
# Uso na VM: sudo bash /opt/syntexa/scripts/setup_redis_vm.sh
set -euo pipefail
ROOT="${ROOT:-/opt/syntexa}"
ENV_FILE="$ROOT/.env"

export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y redis-server

# Garantir bind local (Jammy costuma já vir assim)
if grep -q '^bind ' /etc/redis/redis.conf 2>/dev/null; then
  sed -i 's/^bind .*/bind 127.0.0.1 ::1/' /etc/redis/redis.conf || true
fi
systemctl enable redis-server
systemctl restart redis-server

if [[ -f "$ENV_FILE" ]]; then
  if grep -q '^REDIS_URL=$' "$ENV_FILE" 2>/dev/null || ! grep -q '^REDIS_URL=' "$ENV_FILE" 2>/dev/null; then
    sed -i '/^REDIS_URL=/d' "$ENV_FILE" 2>/dev/null || true
    echo 'REDIS_URL=redis://127.0.0.1:6379/0' >> "$ENV_FILE"
    echo "[OK] REDIS_URL definido em $ENV_FILE"
  else
    echo "[INFO] REDIS_URL já tem valor — não alterado."
  fi
else
  echo "[AVISO] $ENV_FILE ausente — crie e defina REDIS_URL=redis://127.0.0.1:6379/0"
fi

redis-cli ping
echo "[OK] Redis ativo em 127.0.0.1:6379"
