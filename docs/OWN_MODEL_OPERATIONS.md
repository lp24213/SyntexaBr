# Syntexa Own Model Operations

Este documento descreve operação real da IA própria em paralelo ao stack atual.

## Objetivo

- Não remover Ollama/LLM atual.
- Evoluir IA proprietária com:
  - treino próprio,
  - ativação via registry,
  - inferência local (HTTP),
  - benchmark e tuning de VM.

## Execução rápida

- Treino + ativação:
  - Windows: `scripts/own-model/train-full.ps1`
  - Linux: `scripts/own-model/train-full.sh`
- Subir runtime:
  - Windows: `scripts/own-model/start-own-model.ps1`
  - Linux: `scripts/own-model/start-own-model.sh`
- Benchmark:
  - Windows: `scripts/own-model/benchmark.ps1`
  - Linux: `scripts/own-model/benchmark.sh`
- Verificação rígida (sem fallback em produção):
  - `python scripts/own-model/verify_no_fallback.py`
  - Em produção use também:
    - `ENVIRONMENT=production`
    - `DEFAULT_LLM=syntexa_native`
    - `OWN_MODEL_STRICT_NO_FALLBACK=1`

## Docker

- `docker-compose.own-model.yml`
- `docker/own-model/Dockerfile`

Subida:

```bash
docker compose -f docker-compose.own-model.yml up -d --build
```

## Gateway Node (opcional)

Arquivo: `production-node/own-model-gateway/server.js`

Uso:

```bash
node production-node/own-model-gateway/server.js
```

Variáveis:
- `OWN_MODEL_GATEWAY_PORT` (default `9010`)
- `OWN_MODEL_UPSTREAM` (default `http://127.0.0.1:9000`)

## Registry / Admin API

- `GET /v1/admin/llm/registry`
- `POST /v1/admin/llm/registry/reload`
- `POST /v1/admin/llm/active`
- `POST /v1/admin/llm/promote-blue-green` (promove candidato e faz rollback automático se readiness falhar)
- `POST /v1/admin/llm/promote-canary` (promove candidato e exige N checks consecutivos de readiness)
- `GET /v1/admin/llm/readiness`
- `GET /v1/admin/llm/slo-snapshot` (snapshot de erro/latência/tokens para gate de promoção)

Exemplo de promoção blue/green:

```bash
curl -X POST "http://127.0.0.1:8000/v1/admin/llm/promote-blue-green" \
  -H "Authorization: Bearer <TOKEN_ADMIN>" \
  -H "Content-Type: application/json" \
  -d '{"candidate_model":"syntexa_small","rollback_on_fail":true}'
```

Exemplo canário:

```bash
curl -X POST "http://127.0.0.1:8000/v1/admin/llm/promote-canary" \
  -H "Authorization: Bearer <TOKEN_ADMIN>" \
  -H "Content-Type: application/json" \
  -d '{"candidate_model":"syntexa_small","checks":5,"interval_sec":2.0,"rollback_on_fail":true}'
```

Canário com gate de SLO (já ativado por padrão):
- bloqueia promoção quando:
  - `error_rate` > `max_error_rate` (default `0.08`)
  - `p95_latency_ms` > `max_p95_latency_ms` (default `3500`)
  - `requests_total` < `min_requests_for_slo` (default `50`)

Auditoria de promoção:
- eventos em `audit_logs`:
  - `llm_promote_blue_green`
  - `llm_promote_canary`

## Alertas operacionais de runtime

Quando o chat falhar por indisponibilidade real do runtime em ambiente de produção/estrito, o backend envia alerta por e-mail.

Variáveis:
- `OPS_ALERT_EMAIL` (destinatário preferencial; fallback para `VEREDA_ADMIN_EMAIL`)
- `CHAT_RUNTIME_ALERT_COOLDOWN_SEC` (anti-spam; default `120`)
- `OWN_MODEL_WATCHDOG_ENABLED` (habilita monitor de readiness em background; default `1`)
- `OWN_MODEL_WATCHDOG_INTERVAL_SEC` (intervalo de checagem; default `60`)

## Métricas Prometheus

Endpoint:
- `GET /metrics`

Métricas-chave:
- `syntexa_runtime_ready` (`1` pronto, `0` indisponível)
- `syntexa_runtime_strict_no_fallback` (`1` modo estrito)
- `syntexa_runtime_last_check_unix` (timestamp da última checagem do watchdog)

## Stack de observabilidade (Prometheus + Alertmanager + Grafana)

Arquivos:
- `monitoring/prometheus/prometheus.yml`
- `monitoring/prometheus/alert_rules.yml`
- `monitoring/alertmanager/alertmanager.yml`
- `monitoring/grafana/provisioning/*`
- `monitoring/grafana/dashboards/syntexa-own-model-overview.json`

Subir stack completa:

```bash
docker compose -f docker-compose.own-model-full.yml up -d --build
```

Endpoints:
- Prometheus: `http://localhost:9090`
- Alertmanager: `http://localhost:9093`
- Grafana: `http://localhost:3000`

Webhook de alerta (Discord/Slack bridge/webhook receiver):
- Defina `ALERT_WEBHOOK_URL` no `.env`
- Exemplo: `ALERT_WEBHOOK_URL=https://seu-endpoint-de-alerta/webhook`

Alertas prontos:
- `SyntexaRuntimeDown` quando `syntexa_runtime_ready == 0` por `2m`
- `SyntexaNoFallbackDisabled` quando `syntexa_runtime_strict_no_fallback == 0` por `5m`

Métricas adicionais de chat (SRE):
- `syntexa_chat_requests_total{endpoint,status}`
- `syntexa_chat_errors_total{endpoint,error_type}`
- `syntexa_chat_latency_ms_sum{endpoint}`
- `syntexa_chat_latency_ms_count{endpoint}`
- `syntexa_chat_latency_ms_bucket{endpoint,le}` (histogram para p50/p95/p99)
- `syntexa_chat_tokens_total{endpoint,token_type}`

Alertas SRE adicionais:
- `SyntexaChatHighErrorRate` (erro > 5% por 5m)
- `SyntexaChatHighP95Latency` (p95 > 3000ms por 10m)

## Bundle de runtime

```bash
python training/export_runtime_bundle.py --manifest checkpoints/syntexa_small/manifest.json --out-dir dist/own-model-bundle
```

Assinar e validar bundle:

```bash
python scripts/own-model/sign_runtime_bundle.py --bundle-dir dist/own-model-bundle
python scripts/own-model/verify_runtime_bundle.py --bundle-dir dist/own-model-bundle
```

Export com assinatura embutida:

```bash
python training/export_runtime_bundle.py --manifest checkpoints/syntexa_small/manifest.json --out-dir dist/own-model-bundle --sign
```

## Runbook enterprise (scripts)

- Canary promotion:
  - `scripts/own-model/promote_canary.sh`
  - `scripts/own-model/promote_canary.ps1`
- Preflight de produção:
  - `scripts/own-model/preflight_enterprise.sh`
  - `scripts/own-model/preflight_enterprise.ps1`
- Backup/restore de registry:
  - `scripts/own-model/backup_registry.sh` / `restore_registry.sh`
  - `scripts/own-model/backup_registry.ps1` / `restore_registry.ps1`
- Disaster recovery backup completo:
  - `scripts/own-model/disaster_recovery_backup.sh`
  - `scripts/own-model/disaster_recovery_backup.ps1`
- Monitor pós deploy com rollback automático por SLO:
  - `scripts/own-model/monitor_post_deploy.sh`
  - `scripts/own-model/monitor_post_deploy.ps1`
