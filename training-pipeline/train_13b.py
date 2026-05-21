#!/usr/bin/env python3
"""
SYNTEXA 13B TRAINING PIPELINE
==============================
Treinamento completo da Foundation Model 13B.
Requisitos mínimos: GPU A100 80GB ou 2x A100 40GB.
Com DeepSpeed ZeRO-3, é possível treinar em 4x A100 40GB.
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

from vereda_ai.syntexa_core.foundation_model import SyntexaFoundationConfig, get_13b_config
from vereda_ai.syntexa_core.foundation_trainer import SyntexaFoundationTrainer, TrainingConfig
from vereda_ai.syntexa_core.foundation_tokenizer import SyntexaFoundationTokenizer

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def main() -> None:
    ap = argparse.ArgumentParser(description="Treinamento Syntexa 13B")
    ap.add_argument("--data", required=True, help="JSONL com campo 'text'")
    ap.add_argument("--output-dir", default="checkpoints/foundation_13b", help="Diretório de saída")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--batch-size", type=int, default=2, help="Reduzir se OOM (1 para 80GB)")
    ap.add_argument("--gradient-accumulation", type=int, default=8)
    ap.add_argument("--seq-len", type=int, default=2048)
    ap.add_argument("--lr", type=float, default=1.5e-4)
    ap.add_argument("--weight-decay", type=float, default=0.1)
    ap.add_argument("--max-grad-norm", type=float, default=1.0)
    ap.add_argument("--warmup-steps", type=int, default=500)
    ap.add_argument("--checkpoint-every", type=int, default=250)
    ap.add_argument("--resume", default=None, help="Checkpoint para retomar")
    ap.add_argument("--sft-data", default=None, help="JSONL para SFT (instruction tuning)")
    ap.add_argument("--sft-epochs", type=int, default=2)
    ap.add_argument("--deepspeed-config", default=None, help="Path para deepspeed config JSON")
    ap.add_argument("--dtype", default="bfloat16", choices=["float16", "bfloat16", "float32"])
    ap.add_argument("--device", default=None)
    args = ap.parse_args()

    dtype_map = {"float16": torch.float16, "bfloat16": torch.bfloat16, "float32": torch.float32}
    dtype = dtype_map[args.dtype]

    model_cfg = get_13b_config(dtype=dtype)

    train_cfg = TrainingConfig(
        data_path=args.data,
        output_dir=args.output_dir,
        tokenizer_dir=f"{args.output_dir}/tokenizer",
        model_config=model_cfg,
        epochs=args.epochs,
        batch_size=args.batch_size,
        max_seq_len=args.seq_len,
        learning_rate=args.lr,
        weight_decay=args.weight_decay,
        max_grad_norm=args.max_grad_norm,
        warmup_steps=args.warmup_steps,
        checkpoint_every_steps=args.checkpoint_every,
        use_amp=(dtype != torch.float32),
        dtype=dtype,
        device=args.device,
    )

    trainer = SyntexaFoundationTrainer(train_cfg)

    if args.resume:
        log.info("Retomando de checkpoint: %s", args.resume)
        trainer.load_checkpoint(args.resume)

    log.info("=" * 60)
    log.info("SYNTEXA 13B TRAINING")
    log.info("Parameters: %s", f"{sum(p.numel() for p in trainer.model.parameters()):,}")
    log.info("Output: %s", args.output_dir)
    log.info("=" * 60)

    # Pretraining
    trainer.train()

    # SFT opcional
    if args.sft_data:
        log.info("Iniciando SFT com %s", args.sft_data)
        trainer.train_sft(args.sft_data, epochs=args.sft_epochs)

    # Salva final
    paths = trainer.save_final(name="syntexa_13b")
    log.info("=" * 60)
    log.info("Treinamento concluído!")
    log.info("  Weights: %s", paths["weights"])
    log.info("  Manifest: %s", paths["manifest"])
    log.info("  Tokenizer: %s", paths["tokenizer"])
    log.info("=" * 60)

    # Info de inferência
    info = {
        "name": "syntexa_13b",
        "parameters": sum(p.numel() for p in trainer.model.parameters()),
        "checkpoint": str(paths["weights"]),
        "tokenizer": str(paths["tokenizer"]),
        "manifest": str(paths["manifest"]),
    }
    (Path(args.output_dir) / "inference_info.json").write_text(
        json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
