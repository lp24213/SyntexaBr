#!/bin/bash
set -e
cd /opt/syntexa-worker
. .venv/bin/activate

echo "=== smoke ==="
PYTHONPATH=/opt/syntexa-worker python - <<'PY'
import os, sys
sys.path.insert(0, "/opt/syntexa-worker")
import json
from vereda_ai.syntexa_core.foundation_inference import SyntexaInferenceEngine
from vereda_ai.syntexa_core.foundation_model import SyntexaFoundationConfig
m = json.load(open("/opt/syntexa-worker/checkpoints/foundation/manifest.json"))
cfg = SyntexaFoundationConfig(
    vocab_size=int(m["vocab_size"]),
    dim=int(m["dim"]),
    num_layers=int(m["num_layers"]),
    num_heads=int(m["num_heads"]),
    num_kv_heads=int(m.get("num_kv_heads", m["num_heads"])),
    max_seq_len=int(m["max_seq_len"]),
)
e = SyntexaInferenceEngine()
e.load_from_checkpoint(
    "/opt/syntexa-worker/checkpoints/foundation/checkpoint_sft_ep20.pt",
    "/opt/syntexa-worker/checkpoints/foundation/tokenizer",
    cfg,
)
out = e.chat([{"role":"user","content":"Ola"}], max_new_tokens=20)
print("OUTPUT:", repr(out))
PY

echo "=== systemd worker ==="
sudo tee /etc/systemd/system/syntexa-worker.service >/dev/null <<'EOF'
[Unit]
Description=Syntexa Native Worker
After=network-online.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/syntexa-worker
Environment=PYTHONPATH=/opt/syntexa-worker
Environment=SYNTEXA_CHECKPOINT_PATH=/opt/syntexa-worker/checkpoints/foundation/checkpoint_sft_ep20.pt
Environment=SYNTEXA_TOKENIZER_DIR=/opt/syntexa-worker/checkpoints/foundation/tokenizer
Environment=SYNTEXA_MANIFEST_PATH=/opt/syntexa-worker/checkpoints/foundation/manifest.json
ExecStart=/opt/syntexa-worker/.venv/bin/python -m uvicorn infrastructure.syntexa-native-worker.server:app --host 127.0.0.1 --port 8001
Restart=always
RestartSec=5
StandardOutput=append:/var/log/syntexa-worker.log
StandardError=append:/var/log/syntexa-worker.log

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/syntexa-tunnel.service >/dev/null <<'EOF'
[Unit]
Description=Cloudflare Quick Tunnel
After=syntexa-worker.service

[Service]
Type=simple
ExecStart=/usr/local/bin/cloudflared tunnel --no-autoupdate --url http://127.0.0.1:8001
Restart=always
RestartSec=5
StandardOutput=append:/var/log/syntexa-tunnel.log
StandardError=append:/var/log/syntexa-tunnel.log

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now syntexa-worker.service
sleep 6
sudo systemctl enable --now syntexa-tunnel.service
sleep 15

echo "=== worker status ==="
sudo systemctl is-active syntexa-worker
echo "=== tunnel status ==="
sudo systemctl is-active syntexa-tunnel
echo "=== local health ==="
curl -sS http://127.0.0.1:8001/health || true
echo
echo "=== tunnel URL ==="
grep -Eo 'https://[a-z0-9-]+\.trycloudflare\.com' /var/log/syntexa-tunnel.log | head -1 || echo "(retry in 30s)"
