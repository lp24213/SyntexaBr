#!/usr/bin/env python3
"""
SYNTEXA BUDGET TRAINING ($100 AWS)
====================================
Treinamento otimizado para orçamento limitado.
Treina Syntexa Small (~1.1B) que cabe em GPU modesta (A10G 24GB).
Ideal para iterar rápido e validar o pipeline antes de escalar.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from vereda_ai.syntexa_core.foundation_model import SyntexaFoundationConfig
from vereda_ai.syntexa_core.foundation_trainer import SyntexaFoundationTrainer, TrainingConfig

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def get_small_config(dtype: torch.dtype = torch.bfloat16) -> SyntexaFoundationConfig:
    """~1.1B params. Caba em A10G 24GB com batch_size=8 e AMP."""
    return SyntexaFoundationConfig(
        vocab_size=32000,
        dim=2048,
        num_layers=22,
        num_heads=16,
        num_kv_heads=4,  # GQA agressivo para reduzir memória
        max_seq_len=4096,
        hidden_dim=5504,
        rope_theta=10000.0,
        dropout=0.1,
        dtype=dtype,
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Treinamento Syntexa Budget (~1.1B)")
    ap.add_argument("--data", required=True, help="JSONL com campo 'text'")
    ap.add_argument("--output-dir", default="checkpoints/foundation_budget", help="Diretório de saída")
    ap.add_argument("--epochs", type=int, default=5)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--seq-len", type=int, default=2048)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--sft-data", default=None, help="JSONL para SFT")
    ap.add_argument("--sft-epochs", type=int, default=2)
    ap.add_argument("--resume", default=None)
    args = ap.parse_args()

    model_cfg = get_small_config(dtype=torch.bfloat16)

    train_cfg = TrainingConfig(
        data_path=args.data,
        output_dir=args.output_dir,
        tokenizer_dir=f"{args.output_dir}/tokenizer",
        model_config=model_cfg,
        epochs=args.epochs,
        batch_size=args.batch_size,
        max_seq_len=args.seq_len,
        learning_rate=args.lr,
        use_amp=True,
        dtype=torch.bfloat16,
    )

    trainer = SyntexaFoundationTrainer(train_cfg)

    if args.resume:
        trainer.load_checkpoint(args.resume)

    log.info("=" * 60)
    log.info("SYNTEXA BUDGET TRAINING (~1.1B params)")
    log.info("VRAM estimada: ~18GB (cab em A10G 24GB)")
    log.info("Custo AWS spot g5.xlarge: ~$0.50/hora")
    log.info("50 horas de treino = ~$25")
    log.info("=" * 60)

    trainer.train()

    if args.sft_data:
        log.info("Iniciando SFT...")
        trainer.train_sft(args.sft_data, epochs=args.sft_epochs)

    paths = trainer.save_final(name="syntexa_budget")
    log.info("Concluído! Weights: %s", paths["weights"])


if __name__ == "__main__":
    main()
