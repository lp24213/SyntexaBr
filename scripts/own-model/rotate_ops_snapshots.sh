#!/usr/bin/env bash
# Mantém apenas os N ficheiros mais recentes por prefixo (readiness-, slo-, ...).
set -euo pipefail
DIR="${1:-./artifacts/ops-snapshots}"
KEEP="${2:-24}"
if [ ! -d "${DIR}" ]; then
  echo "Diretório inexistente: ${DIR}"
  exit 0
fi
for prefix in readiness slo policy registry; do
  mapfile -t files < <(ls -1t "${DIR}/${prefix}-"*.json 2>/dev/null || true)
  if [ "${#files[@]}" -le "${KEEP}" ]; then
    continue
  fi
  for ((i = KEEP; i < ${#files[@]}; i++)); do
    echo "[rotate] rm ${files[$i]}"
    rm -f "${files[$i]}"
  done
done
echo "[rotate] concluído (keep=${KEEP})"
