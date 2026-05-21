#!/bin/bash
# Roda em /opt/syntexa-worker depois do scp do payload.
set -e
exec > >(tee /var/log/syntexa-setup.log) 2>&1
cd /opt/syntexa-worker

echo "[setup] $(date -u)"

# venv + deps
python3.11 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip wheel setuptools
pip install --no-cache-dir -r infrastructure/syntexa-native-worker/requirements.txt

# Smoke test: pode importar e carregar checkpoint?
python - <<'PY'
import sys, os
os.environ.setdefault("SYNTEXA_CHECKPOINT_PATH", "/opt/syntexa-worker/checkpoints/foundation/checkpoint_sft_ep20.pt")
os.environ.setdefault("SYNTEXA_TOKENIZER_DIR", "/opt/syntexa-worker/checkpoints/foundation/tokenizer")
os.environ.setdefault("SYNTEXA_MANIFEST_PATH", "/opt/syntexa-worker/checkpoints/foundation/manifest.json")
sys.path.insert(0, "/opt/syntexa-worker")
from vereda_ai.syntexa_core.foundation_inference import SyntexaInferenceEngine
from vereda_ai.syntexa_core.foundation_model import SyntexaFoundationConfig
import json
m = json.load(open(os.environ["SYNTEXA_MANIFEST_PATH"]))
cfg = SyntexaFoundationConfig(
    vocab_size=int(m.get("vocab_size",532)),
    dim=int(m.get("dim",128)),
    num_layers=int(m.get("num_layers",2)),
    num_heads=int(m.get("num_heads",2)),
    num_kv_heads=int(m.get("num_kv_heads",m.get("num_heads",2))),
    max_seq_len=int(m.get("max_seq_len",256)),
)
e = SyntexaInferenceEngine()
e.load_from_checkpoint(os.environ["SYNTEXA_CHECKPOINT_PATH"], os.environ["SYNTEXA_TOKENIZER_DIR"], cfg)
out = e.chat([{"role":"user","content":"Olá"}], max_new_tokens=16)
print("SMOKE_OK:", repr(out)[:200])
PY

# systemd unit
sudo tee /etc/systemd/system/syntexa-worker.service >/dev/null <<'EOF'
[Unit]
Description=Syntexa Native Worker (motor proprietario syntexa_native)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/syntexa-worker
Environment=PYTHONPATH=/opt/syntexa-worker
Environment=SYNTEXA_CHECKPOINT_PATH=/opt/syntexa-worker/checkpoints/foundation/checkpoint_sft_ep20.pt
Environment=SYNTEXA_TOKENIZER_DIR=/opt/syntexa-worker/checkpoints/foundation/tokenizer
Environment=SYNTEXA_MANIFEST_PATH=/opt/syntexa-worker/checkpoints/foundation/manifest.json
ExecStart=/opt/syntexa-worker/.venv/bin/uvicorn infrastructure.syntexa-native-worker.server:app --host 127.0.0.1 --port 8001 --workers 1
Restart=always
RestartSec=5
StandardOutput=append:/var/log/syntexa-worker.log
StandardError=append:/var/log/syntexa-worker.log

[Install]
WantedBy=multi-user.target
EOF

# cloudflared quick tunnel
sudo tee /etc/systemd/system/syntexa-tunnel.service >/dev/null <<'EOF'
[Unit]
Description=Cloudflare Quick Tunnel for Syntexa Worker
After=syntexa-worker.service
Requires=syntexa-worker.service

[Service]
Type=simple
ExecStart=/usr/local/bin/cloudflared tunnel --no-autoupdate --url http://127.0.0.1:8001 --metrics 127.0.0.1:36500
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
sleep 12

echo "[setup] worker status:"
sudo systemctl is-active syntexa-worker
echo "[setup] tunnel status:"
sudo systemctl is-active syntexa-tunnel
echo "[setup] tunnel URL (extract):"
grep -Eo 'https://[a-z0-9-]+\.trycloudflare\.com' /var/log/syntexa-tunnel.log | head -1 || echo "(aguarde mais alguns segundos)"
echo "[setup] DONE $(date -u)"
