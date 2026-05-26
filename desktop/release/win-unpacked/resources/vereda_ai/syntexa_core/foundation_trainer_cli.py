#!/usr/bin/env python3
"""
SYNTEXA FOUNDATION TRAINER CLI
==============================
Script de treinamento da foundation model soberana.
Uso:
    python -m vereda_ai.syntexa_core.foundation_trainer_cli \
        --data dataset.jsonl \
        --output-dir checkpoints/foundation \
        --epochs 3 \
        --batch-size 8 \
        --dim 1024 --layers 16 --heads 16
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import torch

# Adiciona root ao path
_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from vereda_ai.syntexa_core.foundation_model import SyntexaFoundationConfig
from vereda_ai.syntexa_core.foundation_trainer import SyntexaFoundationTrainer, TrainingConfig

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def main() -> None:
    ap = argparse.ArgumentParser(description="Treinamento Foundation Model Syntexa")
    ap.add_argument("--data", required=True, help="JSONL com campo 'text'")
    ap.add_argument("--output-dir", default="checkpoints/foundation", help="Diretório de saída")
    ap.add_argument("--tokenizer-dir", default=None, help="Diretório do tokenizer (gera se não informado)")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--batch-size", type=int, default=8)
    ap.add_argument("--seq-len", type=int, default=2048)
    ap.add_argument("--steps-per-epoch", type=int, default=None, help="Se None, calcula automaticamente")
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--weight-decay", type=float, default=0.1)
    ap.add_argument("--max-grad-norm", type=float, default=1.0)
    ap.add_argument("--warmup-steps", type=int, default=100)
    ap.add_argument("--checkpoint-every", type=int, default=500)
    ap.add_argument("--vocab-size", type=int, default=32000)
    ap.add_argument("--dim", type=int, default=1024, help="Dimensão do modelo")
    ap.add_argument("--layers", type=int, default=16, help="Número de camadas")
    ap.add_argument("--heads", type=int, default=16, help="Número de heads de atenção")
    ap.add_argument("--kv-heads", type=int, default=None, help="Heads KV para GQA (default = heads)")
    ap.add_argument("--max-seq-len", type=int, default=8192)
    ap.add_argument("--device", default=None)
    ap.add_argument("--use-amp", action="store_true", default=True, help="Mixed precision (fp16)")
    ap.add_argument("--no-amp", dest="use_amp", action="store_false")
    ap.add_argument("--sft-data", default=None, help="JSONL para SFT (instruction tuning)")
    ap.add_argument("--sft-epochs", type=int, default=2)
    ap.add_argument("--resume", default=None, help="Caminho do checkpoint para retomar treino")
    args = ap.parse_args()

    model_cfg = SyntexaFoundationConfig(
        vocab_size=args.vocab_size,
        dim=args.dim,
        num_layers=args.layers,
        num_heads=args.heads,
        num_kv_heads=args.kv_heads,
        max_seq_len=args.max_seq_len,
    )

    train_cfg = TrainingConfig(
        data_path=args.data,
        output_dir=args.output_dir,
        tokenizer_dir=args.tokenizer_dir or f"{args.output_dir}/tokenizer",
        model_config=model_cfg,
        epochs=args.epochs,
        batch_size=args.batch_size,
        max_seq_len=args.seq_len,
        learning_rate=args.lr,
        weight_decay=args.weight_decay,
        max_grad_norm=args.max_grad_norm,
        warmup_steps=args.warmup_steps,
        checkpoint_every_steps=args.checkpoint_every,
        use_amp=args.use_amp,
        dtype=torch.float16 if args.use_amp else torch.float32,
        device=args.device,
    )

    trainer = SyntexaFoundationTrainer(train_cfg)

    if args.resume:
        log.info("Retomando de checkpoint: %s", args.resume)
        trainer.load_checkpoint(args.resume)

    # Treinamento principal (pretraining)
    trainer.train(steps_per_epoch=args.steps_per_epoch)

    # SFT opcional
    if args.sft_data:
        log.info("Iniciando SFT com %s", args.sft_data)
        trainer.train_sft(args.sft_data, epochs=args.sft_epochs)

    # Salva modelo final
    paths = trainer.save_final(name="syntexa_foundation")
    log.info("=" * 60)
    log.info("Treinamento concluído!")
    log.info("  Weights: %s", paths["weights"])
    log.info("  Manifest: %s", paths["manifest"])
    log.info("  Tokenizer: %s", paths["tokenizer"])
    log.info("=" * 60)


if __name__ == "__main__":
    main()
