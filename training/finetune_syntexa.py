#!/usr/bin/env python3
"""Fine-tune a partir de checkpoint Syntexa próprio."""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description="Fine-tune Syntexa")
    ap.add_argument("--base-checkpoint", required=True, help="Checkpoint .pt ou pasta HuggingFace-style própria")
    ap.add_argument("--data", required=True, help="JSONL")
    ap.add_argument("--out", default="checkpoints/finetune")
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--steps-per-epoch", type=int, default=200)
    args = ap.parse_args()
    base = Path(args.base_checkpoint)
    if not base.exists():
        raise SystemExit(f"Checkpoint base não encontrado: {base}")
    here = Path(__file__).resolve().parent
    train = here / "train_small_model.py"
    cmd = [
        sys.executable,
        str(train),
        "--data",
        args.data,
        "--checkpoints",
        args.out,
        "--epochs",
        str(args.epochs),
        "--batch-size",
        str(args.batch_size),
        "--steps-per-epoch",
        str(args.steps_per_epoch),
    ]
    print("Executando:", " ".join(cmd))
    subprocess.run(cmd, check=False)


if __name__ == "__main__":
    main()
