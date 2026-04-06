/**
 * PM2 no Hetzner — usar nome ecosystem.config.* para o PM2 interpretar como apps (não como script Node).
 * No servidor:
 *   pm2 delete all
 *   pkill -f "uvicorn vereda_backend" || true
 *   cd /opt/syntexa && pm2 start scripts/ecosystem.config.cjs && pm2 save
 */
module.exports = {
  apps: [
    {
      name: "syntexa-backend",
      cwd: "/opt/syntexa",
      script: "/opt/syntexa/.venv/bin/python",
      args: "-m uvicorn vereda_backend.main:app --host 0.0.0.0 --port 8000",
      interpreter: "none",
      instances: 1,
      autorestart: true,
      max_restarts: 100,
      min_uptime: "15s",
      env: {
        PYTHONPATH: "/opt/syntexa",
        PYTHONDONTWRITEBYTECODE: "1",
      },
    },
  ],
};
