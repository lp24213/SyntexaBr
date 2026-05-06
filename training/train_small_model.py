#!/usr/bin/env python3
"""
Treino do modelo proprietário Syntexa (decoder Transformer), sem importar pesos de terceiros.
Pipeline:
- treina tokenizer próprio do corpus
- constrói lotes autoregressivos (next-token prediction)
- grava weights + manifest para runtime interno
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from vereda_ai.syntexa_core.model_manifest import ModelManifest
from vereda_ai.syntexa_core.tokenizer import SyntexaTokenizer

try:
    import torch
    import torch.nn.functional as F
except Exception:  # pragma: no cover
    torch = None
    F = None

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
from training.model_syntexa import SyntexaConfig, SyntexaDecoderLM


def _load_jsonl_texts(path: Path) -> list[str]:
    out: list[str] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        text = str(obj.get("text", "")).strip()
        if len(text) >= 10:
            out.append(text)
    return out


def _sample_batch(
    all_ids: list[list[int]],
    *,
    batch_size: int,
    seq_len: int,
    device: str,
) -> tuple["torch.Tensor", "torch.Tensor"]:
    import random

    xs, ys = [], []
    while len(xs) < batch_size:
        seq = random.choice(all_ids)
        if len(seq) < seq_len + 1:
            continue
        start = random.randint(0, len(seq) - seq_len - 1)
        chunk = seq[start : start + seq_len + 1]
        xs.append(chunk[:-1])
        ys.append(chunk[1:])
    x = torch.tensor(xs, dtype=torch.long, device=device)
    y = torch.tensor(ys, dtype=torch.long, device=device)
    return x, y


def main() -> None:
    ap = argparse.ArgumentParser(description="Treino Syntexa Small (proprietário)")
    ap.add_argument("--data", required=True, help="JSONL com campo text")
    ap.add_argument("--checkpoints", default="checkpoints/small", help="Diretório de checkpoints")
    ap.add_argument("--epochs", type=int, default=1)
    ap.add_argument("--batch-size", type=int, default=4)
    ap.add_argument("--hidden-size", type=int, default=1024, help="Ex.: ~350M com camadas ajustadas")
    ap.add_argument("--layers", type=int, default=16)
    ap.add_argument("--heads", type=int, default=16)
    ap.add_argument("--seq-len", type=int, default=2048)
    ap.add_argument("--vocab-size", type=int, default=32000)
    ap.add_argument("--model-name", default="syntexa_small")
    ap.add_argument("--steps-per-epoch", type=int, default=300)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--device", default="cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu")
    args = ap.parse_args()
    data_path = Path(args.data)
    if not data_path.is_file():
        raise SystemExit(f"Dados não encontrados: {data_path}")
    ckpt = Path(args.checkpoints)
    ckpt.mkdir(parents=True, exist_ok=True)
    tokenizer_path = ckpt / "tokenizer.json"
    manifest_path = ckpt / "manifest.json"
    cuda = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    tok = SyntexaTokenizer.train_from_jsonl(data_path, vocab_size=args.vocab_size)
    tok.save(tokenizer_path)

    manifest = ModelManifest(
        name=args.model_name,
        family="decoder_transformer",
        stage="training_pipeline",
        vocab_size=args.vocab_size,
        hidden_size=args.hidden_size,
        num_layers=args.layers,
        num_heads=args.heads,
        max_seq_len=args.seq_len,
        checkpoint_path=str((ckpt / "weights.pt").resolve()),
        tokenizer_path=str(tokenizer_path.resolve()),
        metadata={"epochs": args.epochs, "batch_size": args.batch_size},
    )
    manifest.to_file(manifest_path)

    if torch is None or F is None:
        print("Torch não está instalado; gerados apenas tokenizer + manifest.")
        print("Para treino real: pip install torch (ambiente GPU recomendado).")
        return

    device = args.device
    if device.startswith("cuda") and not torch.cuda.is_available():
        device = "cpu"
    texts = _load_jsonl_texts(data_path)
    tokenized = [tok.encode(t, add_special_tokens=True, max_length=args.seq_len * 8) for t in texts]
    tokenized = [t for t in tokenized if len(t) > max(4, min(16, args.seq_len // 2))]
    if not tokenized:
        raise SystemExit("Dataset sem amostras suficientes após tokenização.")

    cfg = SyntexaConfig(
        vocab_size=args.vocab_size,
        hidden_size=args.hidden_size,
        num_layers=args.layers,
        num_heads=args.heads,
        max_seq_len=args.seq_len,
        dropout=0.0,
    )
    model = SyntexaDecoderLM(cfg).to(device)
    optim = torch.optim.AdamW(model.parameters(), lr=args.lr, betas=(0.9, 0.95), weight_decay=0.1)

    print("Iniciando treino autoregressivo Syntexa...")
    model.train()
    for ep in range(args.epochs):
        loss_avg = 0.0
        for step in range(args.steps_per_epoch):
            x, y = _sample_batch(tokenized, batch_size=args.batch_size, seq_len=args.seq_len, device=device)
            logits = model(x)
            loss = F.cross_entropy(logits.reshape(-1, logits.size(-1)), y.reshape(-1))
            optim.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optim.step()
            loss_avg += float(loss.item())
            if (step + 1) % 50 == 0:
                print(f"[ep {ep+1}/{args.epochs}] step {step+1}/{args.steps_per_epoch} loss={loss_avg/(step+1):.4f}")

    weights_path = ckpt / "weights.pt"
    torch.save({"model_state": model.state_dict(), "config": cfg.__dict__}, weights_path)
    print("Treino concluído.")
    print(f"  dados: {data_path}")
    print(f"  checkpoints: {ckpt}")
    print(f"  tokenizer: {tokenizer_path}")
    print(f"  manifest: {manifest_path}")
    print(f"  weights: {weights_path}")
    print(f"  epochs={args.epochs} batch={args.batch_size} hidden={args.hidden_size} cuda_devices={cuda or 'CPU'}")


if __name__ == "__main__":
    main()
