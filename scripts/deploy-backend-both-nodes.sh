#!/usr/bin/env bash
# Deploy backend em TODOS os nós listados (mesmo Azure PostgreSQL em cada /opt/syntexa/.env).
# Uso: bash scripts/deploy-backend-both-nodes.sh
# Env: SYNTEXA_PROD_NODES_FILE (defeito: config/syntexa-prod-nodes.txt) + as mesmas de deploy-backend-bash.sh
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NODES_FILE="${SYNTEXA_PROD_NODES_FILE:-$ROOT/config/syntexa-prod-nodes.txt}"
if [[ ! -f "$NODES_FILE" ]]; then
  echo "Falta o ficheiro de nós: $NODES_FILE" >&2
  exit 1
fi
# grep evita perdas com CRLF/última linha em some shells Windows/Git Bash
mapfile -t _NODES < <(grep -vE '^\s*($|#)' "$NODES_FILE" | sed 's/\r$//')
if [[ ${#_NODES[@]} -eq 0 ]]; then
  echo "Nenhum host em: $NODES_FILE" >&2
  exit 1
fi
for line in "${_NODES[@]}"; do
  line="${line#"${line%%[![:space:]]*}"}"; line="${line%"${line##*[![:space:]]}"}"
  host="${line//[$'\r']/}"
  [[ -z "$host" ]] && continue
  echo ""
  echo "========== Nó: $host =========="
  export SYNTEXA_REMOTE_HOST="$host"
  bash "$ROOT/scripts/deploy-backend-bash.sh"
done
echo ""
echo "[OK] deploy backend concluido em ${#_NODES[@]} nó(s) — ficheiro: $NODES_FILE"
