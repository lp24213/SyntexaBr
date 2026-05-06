module.exports = {
  apps: [
    {
      name: "syntexa-own-model",
      cwd: "/opt/syntexa",
      script: "/opt/syntexa/.venv/bin/python",
      args: "training/serve_model.py --checkpoint /opt/syntexa/checkpoints/syntexa_small/manifest.json --host 0.0.0.0 --port 9000 --device cuda",
      interpreter: "none",
      instances: 1,
      autorestart: true,
      max_restarts: 100,
      min_uptime: "20s",
      env: {
        PYTHONPATH: "/opt/syntexa",
        PYTHONDONTWRITEBYTECODE: "1",
      },
    },
    {
      name: "syntexa-own-model-gateway",
      cwd: "/opt/syntexa",
      script: "/usr/bin/node",
      args: "production-node/own-model-gateway/server.js",
      instances: 1,
      autorestart: true,
      max_restarts: 100,
      min_uptime: "20s",
      env: {
        OWN_MODEL_GATEWAY_PORT: "9010",
        OWN_MODEL_UPSTREAM: "http://127.0.0.1:9000",
      },
    },
  ],
};
