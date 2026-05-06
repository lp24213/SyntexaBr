#!/usr/bin/env bash
set -euo pipefail

SRC_FILE="${1:-}"
if [ -z "${SRC_FILE}" ]; then
  echo "Uso: restore_registry.sh <backup_file.json>"
  exit 1
fi
if [ ! -f "${SRC_FILE}" ]; then
  echo "Arquivo não encontrado: ${SRC_FILE}"
  exit 1
fi

cp "${SRC_FILE}" "config/syntexa_model_registry.json"
echo "Registry restaurado em config/syntexa_model_registry.json"
