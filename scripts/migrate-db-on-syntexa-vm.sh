#!/usr/bin/env bash
# Correr migração SQL (migrate_db.py) n UMA VM usando o .env de /opt/syntexa (já com Azure PG).
# Executar APÓS a primeira carga de DATABASE_URL (ex.: após push-pg-url). Várias VM partilham a mesma BD — 1 run basta
# a menos que altere o esquema outra vez.
# Uso: bash scripts/migrate-db-on-syntexa-vm.sh
#   ou: SYNTEXA_REMOTE_HOST=51.124.194.42 bash scripts/migrate-db-on-syntexa-vm.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SSH_KEY="${SYNTEXA_SSH_KEY:-$HOME/.ssh/id_ed25519}"
REMOTE_USER="${SYNTEXA_REMOTE_USER:-azureuser}"
REMOTE_BASE="${SYNTEXA_REMOTE_BASE:-/opt/syntexa}"
REMOTE_HOST="${SYNTEXA_REMOTE_HOST:-${1:-74.163.97.52}}"
if [[ ! -f "$SSH_KEY" ]]; then
  echo "Chave SSH: $SSH_KEY" >&2
  exit 1
fi
echo "==> migrate (Azure PG) em $REMOTE_USER@$REMOTE_HOST:$REMOTE_BASE"
# Só copia o helper Python se existir; no servidor pós-tar já está
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=60 \
  "${REMOTE_USER}@${REMOTE_HOST}" \
  "set -e; cd $REMOTE_BASE; . .venv/bin/activate; python3 scripts/load_env_and_migrate.py"
echo "[OK] migração concluída. As outras réplicas alinham com o mesmo schema (mesmo cluster PG)."
