#!/usr/bin/env bash
# Deploy backend: tar -> scp -> extrai no servidor e corre remote_deploy_back.sh
# Uso (na raiz do repo): bash scripts/deploy-backend-bash.sh
# Env: SYNTEXA_SSH_KEY, SYNTEXA_REMOTE_USER, SYNTEXA_REMOTE_HOST, SYNTEXA_REMOTE_BASE, SYNTEXA_DEPLOY_INCLUDE_ENV
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

TAR_NAME="syntexa-deploy.tar.gz"
SSH_KEY="${SYNTEXA_SSH_KEY:-$HOME/.ssh/id_ed25519}"
REMOTE_USER="${SYNTEXA_REMOTE_USER:-azureuser}"
REMOTE_BASE="${SYNTEXA_REMOTE_BASE:-/opt/syntexa}"
if [[ -n "${SYNTEXA_REMOTE_HOST:-}" ]]; then
  REMOTE_HOST="$SYNTEXA_REMOTE_HOST"
elif [[ -f "$ROOT/azure-vm-host.txt" ]]; then
  REMOTE_HOST="$(tr -d '\r\n' < "$ROOT/azure-vm-host.txt")"
else
  REMOTE_HOST="74.163.97.52"
fi

if [[ ! -f "$SSH_KEY" ]]; then
  echo "Chave SSH nao encontrada: $SSH_KEY (defina SYNTEXA_SSH_KEY)" >&2
  exit 1
fi

: "${TMPDIR:=${TEMP:-/tmp}}"
TAR_PATH="${TMPDIR%/}/$TAR_NAME"
rm -f "$TAR_PATH"

echo "==> tar (exclui .ps1 em scripts/ - evita locks no Windows)"
# Exclui PowerShell de manutencao; o servidor so precisa de .sh
tar -czf "$TAR_PATH" \
  --exclude='scripts/*.ps1' \
  --exclude='*.pyc' \
  vereda_backend vereda_ai llm-server requirements.txt scripts

echo "==> scp -> $REMOTE_USER@$REMOTE_HOST:$REMOTE_BASE/"
ssh-keygen -R "$REMOTE_HOST" 2>/dev/null || true
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30 \
  "${REMOTE_USER}@${REMOTE_HOST}" "sudo mkdir -p $REMOTE_BASE && sudo chown -R ${REMOTE_USER}:${REMOTE_USER} $REMOTE_BASE"

scp -i "$SSH_KEY" -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=30 \
  "$TAR_PATH" "${REMOTE_USER}@${REMOTE_HOST}:$REMOTE_BASE/"

echo "==> remoto: extrair + deploy"
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=accept-new -o ServerAliveInterval=120 \
  "${REMOTE_USER}@${REMOTE_HOST}" \
  "set -e; cd $REMOTE_BASE; sudo tar --overwrite -xzf $TAR_NAME; sudo chown -R ${REMOTE_USER}:${REMOTE_USER} $REMOTE_BASE; bash scripts/remote_deploy_back.sh"

rm -f "$TAR_PATH" || true
echo "[OK] deploy backend concluido em $REMOTE_HOST"
