#!/usr/bin/env python3
"""Treina o maior modelo possível no hardware local (7GB RAM).
Com 7.2 GB RAM -> ~300M params é o limite real para treinamento AdamW.
Resultado: texto semi-coerente, mas é o máximo físico possível aqui.
Quando GPU AWS for liberada, este mesmo script roda 7B+ com --config 7b.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from vereda_ai.syntexa_core.foundation_model import (
    SyntexaFoundationConfig,
    SyntexaFoundationModel,
)
from vereda_ai.syntexa_core.foundation_tokenizer import SyntexaFoundationTokenizer


# ============================================================
# CONFIGURACOES POR TAMANHO
# ============================================================

def get_30m_config() -> SyntexaFoundationConfig:
    """~30M params - cabe em 512MB RAM para treino."""
    return SyntexaFoundationConfig(
        vocab_size=12000,
        dim=512,
        num_layers=10,
        num_heads=8,
        num_kv_heads=2,
        max_seq_len=1024,
        hidden_dim=1376,
        rope_theta=10000.0,
        dropout=0.1,
        dtype=torch.float32,
    )


def get_50m_config() -> SyntexaFoundationConfig:
    """~50M params - cabe em 1GB RAM para treino."""
    return SyntexaFoundationConfig(
        vocab_size=16000,
        dim=768,
        num_layers=12,
        num_heads=12,
        num_kv_heads=3,
        max_seq_len=2048,
        hidden_dim=2048,
        rope_theta=10000.0,
        dropout=0.1,
        dtype=torch.float32,
    )


def get_100m_config() -> SyntexaFoundationConfig:
    """~100M params - cabe em 2GB RAM para treino."""
    return SyntexaFoundationConfig(
        vocab_size=24000,
        dim=1024,
        num_layers=16,
        num_heads=16,
        num_kv_heads=4,
        max_seq_len=2048,
        hidden_dim=2816,
        rope_theta=10000.0,
        dropout=0.1,
        dtype=torch.float32,
    )


def get_300m_config() -> SyntexaFoundationConfig:
    """~300M params - cabe em 7GB RAM para treino."""
    return SyntexaFoundationConfig(
        vocab_size=32000,
        dim=2048,
        num_layers=24,
        num_heads=16,
        num_kv_heads=4,
        max_seq_len=4096,
        hidden_dim=5504,
        rope_theta=10000.0,
        dropout=0.1,
        dtype=torch.float32,
    )


def get_1b_config() -> SyntexaFoundationConfig:
    """~1B params - só cabe em GPU (24GB+)."""
    return SyntexaFoundationConfig(
        vocab_size=32000,
        dim=4096,
        num_layers=32,
        num_heads=32,
        num_kv_heads=8,
        max_seq_len=8192,
        hidden_dim=11008,
        rope_theta=10000.0,
        dropout=0.1,
        dtype=torch.float32,
    )


def get_7b_config() -> SyntexaFoundationConfig:
    """~7B params - requer GPU A100 40GB+."""
    return SyntexaFoundationConfig(
        vocab_size=32000,
        dim=4096,
        num_layers=32,
        num_heads=32,
        num_kv_heads=8,
        max_seq_len=8192,
        hidden_dim=11008,
        rope_theta=10000.0,
        dropout=0.1,
        dtype=torch.bfloat16,
    )


def get_13b_config() -> SyntexaFoundationConfig:
    """~13B params - requer GPU A100 80GB ou 2x A100 40GB."""
    return SyntexaFoundationConfig(
        vocab_size=32000,
        dim=5120,
        num_layers=40,
        num_heads=40,
        num_kv_heads=10,
        max_seq_len=8192,
        hidden_dim=13824,
        rope_theta=10000.0,
        dropout=0.1,
        dtype=torch.bfloat16,
    )


# ============================================================
# DATASET
# ============================================================

class TextDataset(Dataset):
    def __init__(self, texts: list[str], tokenizer, max_len: int = 512):
        self.samples = []
        for text in texts:
            toks = tokenizer.encode(text, add_special_tokens=True)
            if len(toks) < 10:
                continue
            # Sliding window
            for i in range(0, len(toks) - max_len, max_len // 2):
                chunk = toks[i : i + max_len + 1]
                if len(chunk) == max_len + 1:
                    self.samples.append(chunk)
        print(f"[DATASET] {len(self.samples)} samples criados")

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        toks = self.samples[idx]
        x = torch.tensor(toks[:-1], dtype=torch.long)
        y = torch.tensor(toks[1:], dtype=torch.long)
        return x, y


# ============================================================
# TREINAMENTO
# ============================================================

def train(args):
    device = torch.device(args.device)
    print(f"[DEVICE] {device}")
    print(f"[RAM] {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB GPU" if torch.cuda.is_available() else "[RAM] CPU only")

    configs = {
        "30m": get_30m_config,
        "50m": get_50m_config,
        "100m": get_100m_config,
        "300m": get_300m_config,
        "1b": get_1b_config,
        "7b": get_7b_config,
        "13b": get_13b_config,
    }

    cfg_fn = configs.get(args.config)
    if not cfg_fn:
        print(f"[ERRO] Config '{args.config}' nao existe. Opcoes: {list(configs.keys())}")
        sys.exit(1)

    cfg = cfg_fn()
    print(f"[CONFIG] {args.config}: dim={cfg.dim}, layers={cfg.num_layers}, heads={cfg.num_heads}")

    # Estimativa de memoria
    vocab = cfg.vocab_size * cfg.dim
    attn_per_layer = cfg.dim * cfg.dim * (1 + 2 * cfg.num_kv_heads / cfg.num_heads + 1)
    ffn_per_layer = 3 * cfg.dim * cfg.hidden_dim
    total_params = vocab + cfg.num_layers * (attn_per_layer + ffn_per_layer)
    print(f"[PARAMS] ~{total_params / 1e6:.0f}M params")
    mem_gb = total_params * 4 / 1024**3  # float32
    print(f"[MEM] ~{mem_gb:.1f} GB modelo + ~{mem_gb * 3:.1f} GB treino = ~{mem_gb * 4:.1f} GB total")

    # Verifica RAM
    import psutil
    ram_gb = psutil.virtual_memory().available / 1024**3
    if mem_gb * 4 > ram_gb:
        print(f"[ERRO FATAL] Memoria insuficiente: precisa ~{mem_gb * 4:.1f} GB, tem {ram_gb:.1f} GB")
        print("[ERRO FATAL] Use config menor ou adquira GPU")
        sys.exit(1)

    # Tokenizer
    tok_path = Path(args.tokenizer)
    if tok_path.exists():
        tokenizer = SyntexaFoundationTokenizer.load(tok_path)
        print(f"[OK] Tokenizer carregado: {tok_path}")
    else:
        print("[ERRO] Tokenizer nao encontrado. Treine primeiro com generate_real_corpus.py")
        sys.exit(1)

    # Dataset
    print(f"[DATA] Carregando {args.data}...")
    texts = []
    with open(args.data, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                t = str(obj.get("text", "")).strip()
                if len(t) >= 50:
                    texts.append(t)
            except json.JSONDecodeError:
                continue
    print(f"[DATA] {len(texts)} textos carregados")

    dataset = TextDataset(texts, tokenizer, max_len=args.seq_len)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, num_workers=0)

    # Modelo
    print("[MODEL] Criando modelo...")
    model = SyntexaFoundationModel(cfg)
    model = model.to(device)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"[MODEL] {n_params:,} params ({n_params / 1e6:.1f}M)")

    # Otimizador
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=0.1, betas=(0.9, 0.95))

    # Loop
    model.train()
    step = 0
    total_loss = 0.0
    start_time = time.time()

    print("=" * 60)
    print("TREINAMENTO INICIADO")
    print("=" * 60)

    for epoch in range(args.epochs):
        for batch_idx, (x, y) in enumerate(loader):
            x, y = x.to(device), y.to(device)

            optimizer.zero_grad()
            logits, _ = model(x)
            loss = nn.functional.cross_entropy(logits.view(-1, cfg.vocab_size), y.view(-1))
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()

            total_loss += loss.item()
            step += 1

            if step % args.log_every == 0:
                avg_loss = total_loss / args.log_every
                elapsed = time.time() - start_time
                tok_per_sec = (step * args.batch_size * args.seq_len) / elapsed
                print(f"  step {step:>6} | loss {avg_loss:.4f} | {tok_per_sec:.0f} tok/s | {elapsed:.0f}s")
                total_loss = 0.0

            if step % args.save_every == 0:
                ckpt_dir = Path(args.output_dir) / f"step_{step}"
                ckpt_dir.mkdir(parents=True, exist_ok=True)
                torch.save(model.state_dict(), ckpt_dir / "model.pt")
                (ckpt_dir / "config.json").write_text(json.dumps(cfg.__dict__, default=str))
                print(f"  [CKPT] Salvo: {ckpt_dir}")

            if step >= args.max_steps:
                break

        if step >= args.max_steps:
            break

    # Salva final
    final_dir = Path(args.output_dir) / "final"
    final_dir.mkdir(parents=True, exist_ok=True)
    torch.save(model.state_dict(), final_dir / "model.pt")
    (final_dir / "config.json").write_text(json.dumps(cfg.__dict__, default=str))
    tokenizer.save(final_dir / "tokenizer")

    # Gera manifest
    manifest = {
        "name": f"syntexa_{args.config}",
        "params": n_params,
        "params_m": round(n_params / 1e6, 1),
        "config": args.config,
        "steps": step,
        "final_checkpoint": str(final_dir / "model.pt"),
        "tokenizer": str(final_dir / "tokenizer"),
    }
    (final_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

    print("=" * 60)
    print("TREINAMENTO CONCLUIDO")
    print(f"  Steps: {step}")
    print(f"  Params: {n_params:,}")
    print(f"  Checkpoint: {final_dir / 'model.pt'}")
    print(f"  Manifest: {final_dir / 'manifest.json'}")
    print("=" * 60)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="30m", choices=["30m", "50m", "100m", "300m", "1b", "7b", "13b"])
    ap.add_argument("--data", default="data/syntexa_corpus_real.jsonl")
    ap.add_argument("--tokenizer", default="checkpoints/tokenizer")
    ap.add_argument("--output-dir", default="checkpoints/syntexa_local")
    ap.add_argument("--epochs", type=int, default=3)
    ap.add_argument("--batch-size", type=int, default=1)
    ap.add_argument("--seq-len", type=int, default=512)
    ap.add_argument("--lr", type=float, default=3e-4)
    ap.add_argument("--max-steps", type=int, default=5000)
    ap.add_argument("--log-every", type=int, default=50)
    ap.add_argument("--save-every", type=int, default=500)
    ap.add_argument("--device", default="cpu")
    args = ap.parse_args()
    train(args)


if __name__ == "__main__":
    main()
