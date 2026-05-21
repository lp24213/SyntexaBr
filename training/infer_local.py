#!/usr/bin/env python3
"""Inferencia com modelo treinado local (30M params)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import torch

from vereda_ai.syntexa_core.foundation_model import SyntexaFoundationModel, SyntexaFoundationConfig
from vereda_ai.syntexa_core.foundation_tokenizer import SyntexaFoundationTokenizer


def load_model(checkpoint_dir: Path, device: str = "cpu"):
    cfg_dict = json.loads(Path(checkpoint_dir / "config.json").read_text())
    cfg = SyntexaFoundationConfig(**cfg_dict)
    model = SyntexaFoundationModel(cfg)
    model.load_state_dict(torch.load(checkpoint_dir / "model.pt", map_location=device))
    model.to(device)
    model.eval()
    tokenizer = SyntexaFoundationTokenizer.load(checkpoint_dir / "tokenizer")
    return model, tokenizer, cfg


def generate(prompt: str, model, tokenizer, cfg, max_tokens: int = 64, temperature: float = 0.8, device: str = "cpu"):
    input_ids = torch.tensor([tokenizer.encode(prompt)], dtype=torch.long, device=device)
    with torch.no_grad():
        output = model.generate(input_ids, max_new_tokens=max_tokens, temperature=temperature, top_k=50, top_p=0.9)
    return tokenizer.decode(output[0].tolist(), skip_special_tokens=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", default="checkpoints/syntexa_local/final")
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--max-tokens", type=int, default=64)
    ap.add_argument("--temperature", type=float, default=0.8)
    ap.add_argument("--device", default="cpu")
    args = ap.parse_args()

    ckpt = Path(args.checkpoint)
    print(f"[LOAD] Carregando modelo de {ckpt}...")
    model, tokenizer, cfg = load_model(ckpt, args.device)
    print(f"[OK] Modelo: {sum(p.numel() for p in model.parameters()):,} params")

    print(f"[PROMPT] {args.prompt}")
    print("=" * 60)
    response = generate(args.prompt, model, tokenizer, cfg, args.max_tokens, args.temperature, args.device)
    print(response)
    print("=" * 60)


if __name__ == "__main__":
    main()
