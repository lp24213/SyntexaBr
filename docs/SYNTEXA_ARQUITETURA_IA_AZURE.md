# Syntexa AI — Arquitetura Azure + núcleo proprietário

## 1. O que foi alterado (execução no repositório)

| Área | Alteração |
|------|-----------|
| `vereda_ai/syntexa_core/` | Novo pacote: motor híbrido (`hybrid_engine.py`), embeddings determinísticos placeholder, `model_registry.py` + `config/syntexa_model_registry.json`. |
| `vereda_ai/ai/llm_engine.py` | Provedor `SyntexaNativeLLMProvider` (`syntexa_native`) registado **sempre**; Ollama/Azure/HTTP ficam **opcionais**. Produção aceita só `syntexa_native` sem endpoint externo. |
| `vereda_ai/core/config.py` | `DEFAULT_LLM` padrão `syntexa_native`; campo `ENVIRONMENT`. |
| `vereda_backend/core/config.py` | Default `syntexa_native`; validação de produção aceita núcleo proprietário sem URL de Ollama. |
| `vereda_backend/services/llm_client.py` | Health: `syntexa_native` → `status: up`. |
| `training/` | Scripts reais (stubs executáveis): `prepare_ptbr_data.py`, `tokenizer_train.py`, `train_small_model.py`, `finetune_syntexa.py`, `serve_model.py`. |
| `.env.example` | Documentação e default alinhados a `syntexa_native`. |

**Nota honesta:** treinar um LM 350M–7B **do zero** sem dados massivos e sem semanas de GPU é investigação; os scripts são **pipeline** para as VMs GPU Azure. O motor `syntexa_native` dá **resposta imediata** hoje (regras + intents + sumarização extractiva), sem pagar APIs de terceiros.

---

## 2. Arquitetura final (Azure = hardware; cérebro = teu)

```
                    ┌─────────────────────────────────────┐
                    │  Azure (Brasil South / região)      │
                    │  ─────────────────────────────────  │
  Utilizadores      │  Container Apps / AKS (API FastAPI) │
       │            │  PostgreSQL (metadata + logs + RAG) │
       ▼            │  Redis (cache / filas)              │
  Cloudflare        │  Storage Account (blobs, checkpoints)│
  (front + DNS)     │  Monitor / Key Vault / NSG          │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
                    │  Núcleo Syntexa (código)               │
                    │  • syntexa_native (híbrido interno)    │
                    │  • RAG + memória (DB existente)        │
                    │  • training/ → checkpoints próprios    │
                    └──────────────┬──────────────────────┘
                                   │
                    ┌──────────────▼──────────────────────┐
  Opcional          │  VMs GPU NC/ND (treino + inferência) │
  (tua stack)       │  PyTorch, DeepSpeed, checkpoints Blob │
                    └───────────────────────────────────────┘
```

**Regra de ouro:** nada de “cérebro definitivo” de Meta/OpenAI/Google como **única** opção — Ollama com pesos open-weight na **tua** VM é **ponte opcional**, não arquitetura final.

---

## 3. VM GPU Azure — custo/benefício (orientação)

| Série | Uso típico |
|-------|------------|
| **NCv3 (V100)** | Treino / fine-tune médio; bom equilíbrio quando há stock na região. |
| **NC T4 v3** | Inferência e fine-tune menor custo (T4). |
| **ND A100** | Treino distribuído grande — custo alto; reservar para Fase 3+. |

Preços mudam por região e compromisso (spot vs pay-as-you-go). Avaliar **Azure Pricing Calculator** com NCasT4_v3 vs NCv3 na mesma região do Storage/PostgreSQL para minimizar egress.

---

## 4. Roadmap 30 / 90 / 180 dias

| Janela | Entregas |
|--------|----------|
| **30 dias** | `syntexa_native` em produção; ingestão de corpus PT-BR (`prepare_ptbr_data.py`); pgvector/RAG institucional; métricas no Azure Monitor; remover dependência *obrigatória* de Ollama no default. |
| **90 dias** | Tokenizer + primeiro checkpoint “Syntexa Small” (350M–1B) em GPU; `serve_model.py` atrás de ingress privado; fila Redis para jobs longos; checkpoints em Blob. |
| **180 dias** | Escala 3B+; avaliação automática (`evaluation/` a criar); A/B entre native bridge e modelo proprietário; autoscaling de inferência dedicada. |

---

## 5. Como sair da dependência externa total

1. **Já:** `DEFAULT_LLM=syntexa_native` — API não exige Ollama/OpenAI para responder.
2. **Curto prazo:** se usares Ollama na tua VM, é **só** inferência local; substituição por `serve_model.py` quando o checkpoint existir.
3. **Médio prazo:** treino + avaliação só em `training/` + GPU Azure; registry aponta para Blob (`config/syntexa_model_registry.json`).
4. **Longo prazo:** desligar providers HTTP legados no `LLMEngine` quando `syntexa_small` / `syntexa_medium` estiverem estáveis.

---

## 6. Admin — datasets / jobs (Fase 6)

Próxima implementação sugerida (não feita neste PR): endpoints `/v1/admin/training-jobs` + UI mínima para upload de dataset e disparo de job (Azure Container Instances / AKS Job) com logs no Application Insights.

---

*Documento gerado como entrega de arquitetura alinhada ao pedido “Azure = datacenter, cérebro = proprietário”.*
