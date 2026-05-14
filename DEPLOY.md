# VEREDA / SYNTEXA — Deploy Guide v3.0

## Arquitetura Híbrida Soberana

```
Usuário → Cloudflare Workers (Edge) → Railway (Core) → AWS GPU (Inference)
                                            ↓
                                    Local Hybrid (Fallback)
```

## Pré-requisitos

- Docker + Docker Compose
- kubectl + cluster K8s (opcional)
- Node.js 20+ (para Wrangler)
- Python 3.12+
- Contas: Cloudflare, Railway, AWS

## Quick Start (Local)

```bash
# 1. Clone e configure
cp .env.example .env
# Edite .env com suas chaves

# 2. Subir infra local
docker-compose up -d

# 3. Verificar saúde
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
```

## Deploy Completo

```bash
# Deploy tudo (Cloudflare + Railway + AWS + K8s)
./scripts/deploy/deploy-complete.sh production

# Ou passo a passo:
./scripts/deploy/deploy-aws-gpu.sh
./scripts/deploy/deploy-k8s.sh syntexa production
./scripts/deploy/validate-deploy.sh
```

## Componentes

| Componente | URL / Porta | Função |
|-----------|-------------|--------|
| Cloudflare Worker | `api.syntexabr.com.br` | Edge gateway, Zero Trust |
| Railway Backend | `8000` | Core API, Auth, DB |
| AWS GPU vLLM | `8000` | Inferência pesada |
| AWS Embeddings | `8001` | Embeddings GPU |
| AWS Vision | `8002` | Análise de imagem |
| AWS Voice | `8003` | STT/TTS |
| Local Hybrid | `8002` | Fallback Ollama |
| Redis | `6379` | Cache, Filas |
| PostgreSQL | `5432` | Banco de dados |

## Comandos Úteis

```bash
# Logs
docker-compose logs -f gateway
kubectl logs -n syntexa deployment/syntexa-backend --tail=100 -f

# Escalar
docker-compose up -d --scale gateway=3
kubectl scale deployment/syntexa-backend --replicas=5 -n syntexa

# Health
curl https://api.syntexabr.com.br/health
curl https://api.syntexabr.com.br/v1/health/detailed

# GPU stats (AWS)
ssh -i key.pem ubuntu@$AWS_HOST "nvidia-smi"
```

## Troubleshooting

| Problema | Solução |
|---------|---------|
| Gateway timeout | Verificar `PROXY_TIMEOUT_MS` no wrangler.toml |
| GPU indisponível | Verificar circuit breaker: `/v1/health` no Railway |
| Redis cheio | Aumentar `maxmemory` ou limpar cache |
| Fallback ativo | Verificar saúde AWS GPU, aguardar recovery |

## Monitoramento

- Prometheus: `http://prometheus.syntexabr.com.br`
- Grafana: `http://grafana.syntexabr.com.br`
- Alertas: configurados em `monitoring/prometheus/alert_rules.yml`

## Roadmap

- [ ] Quantum layer em produção
- [ ] Multi-GPU scaling automático
- [ ] Federated learning
- [ ] Edge inference WASM
