# Syntexa Own Model Pipeline

Este fluxo cria e executa uma LLM proprietária da Syntexa sem depender de Ollama.

## 1) Preparar dados

```bash
python training/prepare_ptbr_data.py dados/*.txt -o datasets/syntexa_corpus.jsonl
```

## 2) Treinar modelo próprio

```bash
python training/train_small_model.py --data datasets/syntexa_corpus.jsonl --checkpoints checkpoints/syntexa_small --epochs 2 --batch-size 4 --steps-per-epoch 300 --hidden-size 512 --layers 8 --heads 8 --seq-len 512 --vocab-size 32000 --model-name syntexa_small
```

Artefatos gerados:
- `checkpoints/syntexa_small/tokenizer.json`
- `checkpoints/syntexa_small/manifest.json`
- `checkpoints/syntexa_small/weights.pt`

## 3) Avaliar

```bash
python training/evaluate_model.py --manifest checkpoints/syntexa_small/manifest.json --data datasets/syntexa_corpus.jsonl --max-samples 200
```

## 4) Ativar no registry interno (runtime próprio em-processo)

```bash
python training/activate_model.py --name syntexa_small --manifest checkpoints/syntexa_small/manifest.json
```

## 5) Inferência local direta (teste de qualidade/tokens)

```bash
python training/infer_own_model.py --manifest checkpoints/syntexa_small/manifest.json --prompt "Explique planejamento financeiro para PME no Brasil" --max-new-tokens 1024 --temperature 0.8 --top-k 80
```

## 6) Servir endpoint próprio

```bash
python training/serve_model.py --checkpoint checkpoints/syntexa_small/manifest.json --host 0.0.0.0 --port 9000
```

Endpoint:
- `POST /v1/chat/completions`
- `GET /health`
- `POST /v1/chat/completions/stream`

## 7) Migrar backend para modelo próprio

No `.env`, configure:

```env
DEFAULT_LLM=local_http
LOCAL_LLM_ENDPOINT=http://127.0.0.1:9000
LOCAL_HTTP_LLM_MODEL=syntexa_small
```

Com isso, o backend para de depender de Ollama no caminho de texto.

## Smoke test rápido

```bash
python training/smoke_own_model.py
```

## Benchmark de desempenho (latência e tokens/s)

```bash
python training/benchmark_own_model.py --manifest checkpoints/syntexa_small/manifest.json --prompt "Monte um plano empresarial completo" --runs 5 --max-new-tokens 1024 --temperature 0.8 --top-k 80
```

## Preset de VM (qualidade/performance)

```bash
python training/recommend_vm_profile.py --profile quality
```

## Controle admin do registry (sem parar stack)

- `GET /v1/admin/llm/registry`
- `POST /v1/admin/llm/registry/reload`
- `POST /v1/admin/llm/active` com body `{ "model_name": "syntexa_small" }`
