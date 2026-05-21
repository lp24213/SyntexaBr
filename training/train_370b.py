#!/usr/bin/env python3
"""Treinamento Foundation Model Syntexa 370B.
Requer cluster GPU com ~5223 GB RAM total (model + optimizer + grad + activ).
Com DeepSpeed ZeRO-3 + offload: reduz VRAM, aumenta CPU RAM.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from vereda_ai.syntexa_core.foundation_model import get_370b_config, SyntexaFoundationModel, count_parameters, estimate_model_size
from vereda_ai.syntexa_core.foundation_tokenizer import SyntexaFoundationTokenizer
from vereda_ai.syntexa_core.foundation_trainer import SyntexaFoundationTrainer, TrainingConfig


def main() -> None:
    ap = argparse.ArgumentParser(description="Treinamento Syntexa 370B")
    ap.add_argument("--data", required=True, help="JSONL com campo 'text'")
    ap.add_argument("--output-dir", default="checkpoints/foundation_370b")
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--batch-size", type=int, default=1, help="Por device (com gradient accumulation)")
    ap.add_argument("--seq-len", type=int, default=4096)
    ap.add_argument("--steps-per-epoch", type=int, default=10000)
    ap.add_argument("--lr", type=float, default=1e-4)
    ap.add_argument("--checkpoint-every", type=int, default=500)
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--resume", default=None)
    ap.add_argument("--deepspeed-config", default=None, help="Path para deepspeed config JSON")
    args = ap.parse_args()

    cfg = get_370b_config()
    info = estimate_model_size(SyntexaFoundationModel(cfg))
    print("=" * 60)
    print("SYNTEXA 370B TRAINING")
    print("=" * 60)
    print(f"  Params:  {info['parameters']:,} ({info['size_gb']:.1f} GB FP32)")
    print(f"  Layers:  {cfg.num_layers}")
    print(f"  Dim:     {cfg.dim}")
    print(f"  Heads:   {cfg.num_heads} / KV: {cfg.num_kv_heads}")
    print(f"  Seq:     {args.seq_len}")
    print(f"  Batch:   {args.batch_size} per device")
    print(f"  Data:    {args.data}")
    print("=" * 60)

    # Tenta carregar tokenizer existente ou treina novo
    tok_dir = Path(args.output_dir) / "tokenizer"
    if tok_dir.exists() and (tok_dir / "vocab.json").exists():
        tokenizer = SyntexaFoundationTokenizer.load(tok_dir)
        print(f"[OK] Tokenizer carregado: {tok_dir}")
    else:
        print("[INFO] Treinando tokenizer BPE do corpus...")
        import json as _json
        texts = []
        with open(args.data, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = _json.loads(line)
                    t = str(obj.get("text", "")).strip()
                    if len(t) >= 50:
                        texts.append(t)
                except _json.JSONDecodeError:
                    continue
        tokenizer = SyntexaFoundationTokenizer.train(texts, vocab_size=cfg.vocab_size)
        tokenizer.save(tok_dir)
        print(f"[OK] Tokenizer salvo: {tok_dir}")

    train_cfg = TrainingConfig(
        data_path=args.data,
        output_dir=args.output_dir,
        tokenizer_dir=str(tok_dir),
        model_config=cfg,
        epochs=args.epochs,
        batch_size=args.batch_size,
        max_seq_len=args.seq_len,
        learning_rate=args.lr,
        checkpoint_every_steps=args.checkpoint_every,
        use_amp=False,  # 370B com BF16 precisa AMP cuidadoso; ativar manualmente
        dtype=cfg.dtype,
        device=args.device,
    )

    trainer = SyntexaFoundationTrainer(train_cfg)

    if args.resume:
        trainer.load_checkpoint(args.resume)

    # DeepSpeed opcional
    if args.deepspeed_config:
        try:
            import deepspeed
            ds_config = json.loads(Path(args.deepspeed_config).read_text(encoding="utf-8"))
            print(f"[OK] DeepSpeed config carregado: {args.deepspeed_config}")
            # Integração real requer: deepspeed.initialize(model, optimizer, config=ds_config)
            print("[WARN] DeepSpeed integration stub - ativar em ambiente com GPUs")
        except ImportError:
            print("[WARN] DeepSpeed não instalado. Instalar: pip install deepspeed")

    trainer.train(steps_per_epoch=args.steps_per_epoch)
    paths = trainer.save_final(name="syntexa_370b")
    print("=" * 60)
    print("370B TREINAMENTO CONCLUIDO")
    print(f"  Weights: {paths['weights']}")
    print(f"  Manifest: {paths['manifest']}")
    print(f"  Tokenizer: {paths['tokenizer']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
