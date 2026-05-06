# Syntexa Azure Production Stack (Node + BullMQ + Whisper GPU)

Stack pronta para Ubuntu Azure, sem serviços pagos extras:

- Next.js frontend
- Express API
- Redis self-hosted em Docker
- BullMQ para fila
- Worker separado para jobs pesados
- STT local com Faster-Whisper em GPU
- WebSocket para status em tempo real
- Nginx reverse proxy + rate limiting
- Health checks + auto restart + logs estruturados

## Estrutura

```text
production-node/
  docker-compose.yml
  .env.example
  nginx/
    nginx.conf
    conf.d/default.conf
  api/
    Dockerfile
    package.json
    src/
      index.js
      logger.js
      queue.js
      rateLimit.js
  queue-worker/
    Dockerfile
    package.json
    src/worker.js
  worker-stt/
    Dockerfile
    requirements.txt
    app.py
```

## Fluxo

1. Cliente envia áudio para `POST /api/stt/enqueue`
2. API salva arquivo em volume e enfileira no Redis/BullMQ
3. `queue-worker` consome job e chama `stt-service` (Faster-Whisper GPU)
4. Worker publica status via Redis pub/sub (`stt_events`)
5. API recebe evento e envia via WebSocket (`socket.io`) para o frontend

## Deploy Ubuntu Azure (VM)

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl gnupg lsb-release

# Docker
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo $VERSION_CODENAME) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
sudo usermod -aG docker $USER

# NVIDIA runtime (se VM GPU)
distribution=$(. /etc/os-release;echo $ID$VERSION_ID) \
  && curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add - \
  && curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### Subir stack

```bash
cd /opt/syntexa/production-node
cp .env.example .env
# ajuste variáveis (domínio, limites, modelo, etc.)

docker compose build
docker compose up -d
docker compose ps
```

## Health checks

- Nginx: `GET /nginx-health`
- API: `GET /health`
- STT service: `GET /health` (interno em `stt-service:8001`)

## Logs estruturados

- API/Worker: `pino` (JSON)
- Nginx: `json_combined` format

Exemplos:

```bash
docker compose logs -f api
docker compose logs -f queue-worker
docker compose logs -f stt-service
docker compose logs -f nginx
```

## Anti-503 (aplicado)

- Fila assíncrona para jobs pesados (áudio/STT)
- Worker separado com concorrência controlada
- Retries exponenciais em job
- Timeouts explícitos no worker para STT
- Rate limiting no Nginx + API
- Keepalive e upstream tuning no Nginx
- Health checks e restart automático (`unless-stopped`)
- Cache/persistência de resultado por job no Redis (`stt:result:<jobId>`)

## WebSocket (cliente)

Conectar no frontend:

```js
import { io } from "socket.io-client";

const socket = io("https://SEU_DOMINIO", { path: "/socket.io" });
socket.emit("stt:watch", { jobId });
socket.on("stt:status", (event) => {
  console.log(event); // queued/processing/done/failed
});
```

## Endpoints principais

- `POST /api/stt/enqueue` (multipart, campo `audio`)
- `GET /api/stt/status/:jobId`
- `GET /health`
