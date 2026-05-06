# Exemplos Reais de API (Syntexa Core)

## 1) Buscar memória semântica do usuário

```bash
curl -X POST "https://api.syntexabr.com.br/v1/intel/memory/search" \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "quais eram minhas preferências de linguagem para código?",
    "top_k": 5
  }'
```

## 2) Dashboard admin

```bash
curl -X GET "https://api.syntexabr.com.br/v1/admin/dashboard/metrics" \
  -H "Authorization: Bearer TOKEN_ADMIN"
```

## 3) Export de dataset anonimizado

```bash
curl -X GET "https://api.syntexabr.com.br/v1/admin/dataset/export" \
  -H "Authorization: Bearer TOKEN_ADMIN"
```

## 4) Export local para treino

```bash
python scripts/export_training_dataset.py \
  --output training/datasets/syntexa_dialogs.jsonl
```
