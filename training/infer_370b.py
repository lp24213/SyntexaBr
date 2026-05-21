#!/usr/bin/env python3
"""Inferência Syntexa 370B Foundation Model.
Requer cluster GPU com ~696 GB VRAM (BF16) ou ~348 GB (FP8) ou ~174 GB (INT4).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from vereda_ai.syntexa_core.foundation_inference import SyntexaInferenceEngine


def main() -> None:
    ap = argparse.ArgumentParser(description="Inferência Syntexa 370B")
    ap.add_argument("--checkpoint", required=True)
    ap.add_argument("--tokenizer", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--top-k", type=int, default=50)
    ap.add_argument("--top-p", type=float, default=0.9)
    ap.add_argument("--stream", action="store_true")
    ap.add_argument("--device", default="cuda")
    ap.add_argument("--quant", choices=["bf16", "fp8", "int4", "int8"], default="bf16")
    args = ap.parse_args()

    engine = SyntexaInferenceEngine(device=args.device)
    engine.load_from_checkpoint(args.checkpoint, args.tokenizer)
    stats = engine.get_stats()
    print(f"[OK] Modelo carregado. Device: {stats['device']}")

    messages = [{"role": "user", "content": args.prompt}]

    if args.stream:
        print("=" * 60)
        for chunk in engine.chat_stream(
            messages,
            max_new_tokens=args.max_tokens,
            temperature=args.temperature,
            top_k=args.top_k,
            top_p=args.top_p,
        ):
            print(chunk, end="", flush=True)
        print()
    else:
        print("=" * 60)
        resp = engine.chat(
            messages,
            max_new_tokens=args.max_tokens,
            temperature=args.temperature,
            top_k=args.top_k,
            top_p=args.top_p,
        )
        print(resp)

    final = engine.get_stats()
    print("=" * 60)
    print(f"Tokens: {final['tokens_generated']} | Latência: {final['avg_latency_ms']:.1f}ms | Throughput: {final['throughput_tok_per_sec']:.1f} tok/s")
    print("=" * 60)
    engine.shutdown()


if __name__ == "__main__":
    main()
