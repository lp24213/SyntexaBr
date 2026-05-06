#!/usr/bin/env bash
set -euo pipefail

# Provisionamento one-shot para VM Linux (Ubuntu/Debian):
# - instala dependências
# - instala serviço own-model + gateway
# - inicia e habilita no boot

ROOT="${ROOT:-/opt/syntexa}"

echo "[1/6] packages"
apt-get update -y
apt-get install -y python3 python3-venv python3-pip nodejs npm curl

echo "[2/6] python venv"
cd "${ROOT}"
python3 -m venv .venv
"${ROOT}/.venv/bin/pip" install --upgrade pip
"${ROOT}/.venv/bin/pip" install -r requirements.txt -r requirements-research.txt

echo "[3/6] systemd units"
cp "${ROOT}/scripts/syntexa-own-model.service" /etc/systemd/system/syntexa-own-model.service
cp "${ROOT}/scripts/syntexa-own-model-gateway.service" /etc/systemd/system/syntexa-own-model-gateway.service
systemctl daemon-reload

echo "[4/6] health precheck"
"${ROOT}/.venv/bin/python" "${ROOT}/training/infer_own_model.py" \
  --manifest "${ROOT}/checkpoints/syntexa_small/manifest.json" \
  --prompt "Teste de saúde do runtime Syntexa" \
  --max-new-tokens 64 \
  --temperature 0.7 \
  --top-k 50 || true

echo "[5/6] start services"
systemctl enable syntexa-own-model.service syntexa-own-model-gateway.service
systemctl restart syntexa-own-model.service
sleep 2
systemctl restart syntexa-own-model-gateway.service

echo "[6/6] done"
systemctl --no-pager --full status syntexa-own-model.service || true
systemctl --no-pager --full status syntexa-own-model-gateway.service || true
echo "Provisionamento concluído."
