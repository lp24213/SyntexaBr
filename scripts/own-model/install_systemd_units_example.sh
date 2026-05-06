#!/usr/bin/env bash
# Exemplo: instalar units de scripts/own-model/systemd (ajustar SYNTEXA_REPO).
set -euo pipefail
SYNTEXA_REPO="${SYNTEXA_REPO:-/opt/syntexa/syntexabr}"
UNIT_SRC="${SYNTEXA_REPO}/scripts/own-model/systemd"
if [ ! -d "${UNIT_SRC}" ]; then
  echo "Repo não encontrado: ${UNIT_SRC}"
  exit 1
fi
echo "Copiar para /etc/systemd/system/ como root, depois:"
echo "  sed -i \"s|/opt/syntexa/syntexabr|${SYNTEXA_REPO}|g\" /etc/systemd/system/syntexa-*.service"
echo "  systemctl daemon-reload"
echo "  systemctl enable --now syntexa-llm-guard.timer syntexa-ops-snapshot.timer"
echo "Ficheiros em: ${UNIT_SRC}"
