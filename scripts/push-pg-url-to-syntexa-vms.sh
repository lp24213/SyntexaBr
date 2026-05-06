#!/usr/bin/env bash
# Aplica o MESMO DATABASE_URL (Azure PostgreSQL Flexible) em /opt/syntexa/.env em TODAS as VMs.
# Não envia ficheiro .env do PC — só actualiza as linhas DATABASE_URL e VEREDA_DATABASE_URL.
#
# 1) Portal Azure: PostgreSQL → Rede → permitir acesso a partir de cada IP público das duas VMs
# 2) Defina a URL (password com caracteres especiais: use URL-encoding %40 para @, etc.):
#    export SYNTEXA_AZURE_DATABASE_URL='postgresql+psycopg2://USER%40TENANT:PASS@host.postgres.database.azure.com:5432/DATABASE?sslmode=require'
#    bash scripts/push-pg-url-to-syntexa-vms.sh
# Opcional: SYNTEXA_AZURE_DATABASE_URL_FILE=./config/syntexa-pg.url.local  (só 1.ª linha não vazia)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PGURL="${SYNTEXA_AZURE_DATABASE_URL:-}"
if [[ -z "$PGURL" && -n "${SYNTEXA_AZURE_DATABASE_URL_FILE:-}" && -f "${SYNTEXA_AZURE_DATABASE_URL_FILE}" ]]; then
  PGURL=$(grep -v '^\s*#' "${SYNTEXA_AZURE_DATABASE_URL_FILE}" | grep -m1 -E '\S' | tr -d '\r' || true)
  PGURL="${PGURL#"${PGURL%%[![:space:]]*}"}"; PGURL="${PGURL%"${PGURL##*[![:space:]]}"}"
fi
if [[ -z "$PGURL" ]]; then
  echo "Defina SYNTEXA_AZURE_DATABASE_URL ou um ficheiro com SYNTEXA_AZURE_DATABASE_URL_FILE" >&2
  exit 1
fi
case "$PGURL" in
  postgresql*);;
  *) echo "DATABASE_URL deve começar com postgresql (ex. postgresql+psycopg2://...)" >&2; exit 1 ;;
esac

SSH_KEY="${SYNTEXA_SSH_KEY:-$HOME/.ssh/id_ed25519}"
REMOTE_USER="${SYNTEXA_REMOTE_USER:-azureuser}"
REMOTE_BASE="${SYNTEXA_REMOTE_BASE:-/opt/syntexa}"
NODES_FILE="${SYNTEXA_PROD_NODES_FILE:-$ROOT/config/syntexa-prod-nodes.txt}"
if [[ ! -f "$SSH_KEY" ]]; then
  echo "Chave SSH: $SSH_KEY" >&2
  exit 1
fi
if [[ ! -f "$NODES_FILE" ]]; then
  echo "Falta: $NODES_FILE" >&2
  exit 1
fi

FRAG="/tmp/syntexa-pg-fragment-$$.env"
{
  printf 'DATABASE_URL=%s\n' "$PGURL"
  printf 'VEREDA_DATABASE_URL=%s\n' "$PGURL"
} > "$FRAG"
trap 'rm -f "$FRAG"' EXIT

mapfile -t _NODES < <(grep -vE '^\s*($|#)' "$NODES_FILE" | sed 's/\r$//')
if [[ ${#_NODES[@]} -eq 0 ]]; then
  echo "Nenhum host em: $NODES_FILE" >&2
  exit 1
fi
for line in "${_NODES[@]}"; do
  line="${line#"${line%%[![:space:]]*}"}"; line="${line%"${line##*[![:space:]]}"}"
  host="${line//[$'\r']/}"
  [[ -z "$host" ]] && continue
  echo "==> Push PG URL + restart -> $REMOTE_USER@$host"
  scp -i "$SSH_KEY" -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30 \
    "$FRAG" "${REMOTE_USER}@${host}:/tmp/syntexa-pg-fragment.env"
  ssh -i "$SSH_KEY" -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30 \
    "${REMOTE_USER}@${host}" "REMOTE_BASE='${REMOTE_BASE}' bash -s" <<'REMOTE'
set -euo pipefail
cd "$REMOTE_BASE" || { echo "ERRO: $REMOTE_BASE inacessivel" >&2; exit 1; }
if [[ ! -f .env ]]; then
  echo "ERRO: ${REMOTE_BASE}/.env inexistente — crie a partir de .env.example e segredos." >&2
  exit 1
fi
cp -a .env ".env.bak.$(date +%Y%m%d%H%M%S)" || true
# Remove linhas antigas e anexa o par Azure PG (não mexe noutras chaves)
grep -v '^DATABASE_URL=' .env | grep -v '^VEREDA_DATABASE_URL=' | sed 's/\r$//' > .env.new
cat /tmp/syntexa-pg-fragment.env >> .env.new
mv .env.new .env
rm -f /tmp/syntexa-pg-fragment.env
sed -i 's/\r$//' .env
sudo systemctl restart syntexa-backend
for _i in {1..30}; do
  if curl -sf --connect-timeout 2 http://127.0.0.1:8000/health >/dev/null; then
    echo "[OK] $(hostname 2>/dev/null || echo nó): uvicorn a responder"
    break
  fi
  sleep 1
done
if ! curl -sf --connect-timeout 2 http://127.0.0.1:8000/health >/dev/null; then
  echo "[ERRO] Health falhou; journal:" >&2
  sudo journalctl -u syntexa-backend -n 40 --no-pager >&2
  exit 1
fi
curl -s http://127.0.0.1:8000/health | head -c 400; echo
REMOTE
done

echo "[OK] Azure DATABASE_URL sincronizado e serviço reiniciado em todos os nós."
