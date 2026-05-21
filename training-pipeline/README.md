# Syntexa Training Pipeline

Pipeline completo de treinamento da Foundation Model Syntexa.

## Estágios

1. **Data Ingestion** — Coleta e limpeza de corpus
2. **Tokenizer Training** — BPE byte-level no corpus completo
3. **Pre-training** — Treinamento autoregressivo do decoder Transformer
4. **SFT (Supervised Fine-Tuning)** — Instruction tuning com dados curados
5. **Evaluation** — Benchmarks de qualidade
6. **Export** — Exportação para runtime de inferência

## Configurações Suportadas

| Modelo | Parâmetros | Dim | Layers | Heads | VRAM (BF16) | VRAM (4-bit) |
|--------|-----------|-----|--------|-------|-------------|--------------|
| Syntexa Small | 1.1B | 2048 | 22 | 16 | ~4.5 GB | ~1.2 GB |
| Syntexa Medium | 3.8B | 3072 | 32 | 24 | ~15 GB | ~4 GB |
| Syntexa Large | 7B | 4096 | 32 | 32 | ~28 GB | ~7 GB |
| **Syntexa 13B** | **13.2B** | **5120** | **40** | **40** | **~52 GB** | **~14 GB** |
| Syntexa 32B | 32.5B | 7168 | 56 | 56 | ~128 GB | ~34 GB |

## Uso

```bash
# Treinar 13B completo (requer A100 80GB ou 2x A100 40GB)
python -m training-pipeline.train_13b \
  --data data/syntexa_corpus.jsonl \
  --output-dir checkpoints/foundation_13b \
  --epochs 3 --batch-size 2 --gradient-accumulation 8

# Treinar versão Small com $100 AWS (g5.xlarge spot, viável)
python -m training-pipeline.train_small \
  --data data/syntexa_corpus.jsonl \
  --output-dir checkpoints/foundation_small \
  --epochs 5 --batch-size 8

# Inferência local com checkpoint treinado
python -m training-pipeline.serve \
  --checkpoint checkpoints/foundation_13b/checkpoint_best.pt \
  --port 8000
```

## AWS Deploy

```bash
cd infrastructure/aws-gpu-cluster/terraform
terraform init
terraform apply -var="gpu_instance_type=g5.12xlarge" -var="model_name=syntexa-13b"
```

## Nota sobre Orçamento

Com $100 na AWS:
- **Não dá** pra treinar 13B do zero (precisa de ~$5K+ e semanas de treino)
- **Dá** pra treinar Syntexa Small (~1B) em algumas horas
- **Dá** pra rodar inferência de modelos open-source 13B/32B via vLLM por semanas
- **Dá** pra fazer fine-tuning (LoRA/QLoRA) de modelos existentes
