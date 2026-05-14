# Syntexa Sovereign AI — Local Inference Server

## Workflow: Kaggle + Local

```
[Kaggle GPU]              [Local Machine]
     |                          |
  Fine-tune QLoRA               |
     |                          |
  Export adapters               |
     |                          |
  Download .tar.gz ----------> Extract to ./models/
                                   |
                              Load model + adapters
                                   |
                              FastAPI Server
                                   |
                    +------------------------------+
                    | /health  /chat  /reason      |
                    | /agents  /quantum  /v1/*     |
                    +------------------------------+
```

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Place model

After downloading from Kaggle, extract:

```bash
mkdir -p models
tar xzf syntexa-export.tar.gz -C models/
# Results in: models/syntexa-export/merged/
```

### 3. Start server

```bash
# Default
python server.py --model-dir ./models/syntexa-export/merged

# Custom port
python server.py --port 9000

# Multiple instances (different ports)
python server.py --port 8000 --model-dir ./models/model-a
python server.py --port 8001 --model-dir ./models/model-b
```

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | GPU status, model loaded |
| POST | `/chat` | Chat completion |
| POST | `/chat/stream` | Streaming chat (SSE) |
| POST | `/reason` | Step-by-step reasoning |
| POST | `/agents` | Multi-agent orchestration |
| POST | `/quantum` | Quantum-assisted optimization |
| POST | `/v1/chat/completions` | OpenAI API compatible |

## Multi-Environment Strategy

For high throughput without GPU cluster:

1. **Multiple CPU instances** with smaller quantized models (GGUF)
2. **Single GPU instance** with full model for complex queries
3. **Load balancer** (nginx) routes based on complexity
4. **Redis queue** buffers async requests

### Example: 4 environments

```bash
# Env 1: GPU main (complex queries)
CUDA_VISIBLE_DEVICES=0 python server.py --port 8000 --model-dir ./models/syntexa-merged

# Env 2: CPU fast (simple queries)  
CUDA_VISIBLE_DEVICES= python server.py --port 8001 --model-dir ./models/syntexa-gguf-q4

# Env 3: CPU medium
CUDA_VISIBLE_DEVICES= python server.py --port 8002 --model-dir ./models/syntexa-gguf-q5

# Env 4: CPU backup
CUDA_VISIBLE_DEVICES= python server.py --port 8003 --model-dir ./models/syntexa-gguf-q8
```

## Hardware Requirements

| Setup | VRAM | RAM | Notes |
|-------|------|-----|-------|
| 7B Q4 | 6 GB | 8 GB | Minimum GPU |
| 7B FP16 | 14 GB | 16 GB | Good quality |
| 14B Q4 | 10 GB | 12 GB | Better responses |
| 14B FP16 | 28 GB | 32 GB | Best quality |
| CPU only | 0 GB | 32 GB | Slow but works |

## Testing

```bash
curl -X POST http://localhost:8000/health

curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Hello"}]}'

curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Explain quantum computing"}]}'
```
