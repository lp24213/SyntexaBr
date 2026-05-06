#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 <terraform_output_json> [inventory_out]"
  exit 1
fi

TFJSON=$1
OUT=${2:-ansible/inventory.ini}

if ! command -v jq >/dev/null 2>&1; then
  echo "jq is required. Install jq and retry." >&2
  exit 1
fi

PUBLIC_IP=$(jq -r '.public_ip.value' "$TFJSON")
if [ "$PUBLIC_IP" = "null" ] || [ -z "$PUBLIC_IP" ]; then
  echo "could not find public_ip in $TFJSON" >&2
  exit 1
fi

cat > "$OUT" <<EOF
[exllama]
${PUBLIC_IP} ansible_user=azureuser ansible_ssh_private_key_file=~/.ssh/id_rsa

[hetzner]
# Substitua pelo seu servidor Hetzner
#91.98.123.197 ansible_user=root ansible_ssh_private_key_file=~/.ssh/id_rsa
EOF

echo "Wrote inventory to $OUT"
