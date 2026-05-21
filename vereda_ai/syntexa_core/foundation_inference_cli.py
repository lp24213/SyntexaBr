#!/usr/bin/env python3
"""
SYNTEXA FOUNDATION INFERENCE CLI
=================================
CLI de inferência 100% soberana.
Uso:
    python -m vereda_ai.syntexa_core.foundation_inference_cli \
        --checkpoint checkpoints/foundation/syntexa_foundation_weights.pt \
        --tokenizer checkpoints/foundation/tokenizer \
        --prompt "Explique a teoria da relatividade"
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from vereda_ai.syntexa_core.foundation_inference import SyntexaInferenceEngine
from vereda_ai.syntexa_core.foundation_model import SyntexaFoundationConfig

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def main() -> None:
    ap = argparse.ArgumentParser(description="Inferência Foundation Model Syntexa")
    ap.add_argument("--checkpoint", required=True, help="Caminho do checkpoint .pt")
    ap.add_argument("--tokenizer", required=True, help="Diretório do tokenizer")
    ap.add_argument("--prompt", required=True, help="Texto de entrada")
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--temperature", type=float, default=0.7)
    ap.add_argument("--top-k", type=int, default=50)
    ap.add_argument("--top-p", type=float, default=0.9)
    ap.add_argument("--repetition-penalty", type=float, default=1.1)
    ap.add_argument("--stream", action="store_true", help="Streaming token por token")
    ap.add_argument("--system", default=None, help="Mensagem de sistema opcional")
    ap.add_argument("--chat", action="store_true", help="Modo chat (conversa multi-turn)")
    args = ap.parse_args()

    engine = SyntexaInferenceEngine()
    engine.load_from_checkpoint(args.checkpoint, args.tokenizer)
    stats = engine.get_stats()
    log.info("Modelo carregado. Dispositivo: %s", stats["device"])

    messages = []
    if args.system:
        messages.append({"role": "system", "content": args.system})
    messages.append({"role": "user", "content": args.prompt})

    if args.stream:
        print("=" * 60)
        print("RESPOSTA (streaming):")
        print("=" * 60)
        for chunk in engine.chat_stream(
            messages,
            max_new_tokens=args.max_tokens,
            temperature=args.temperature,
            top_k=args.top_k,
            top_p=args.top_p,
            repetition_penalty=args.repetition_penalty,
        ):
            print(chunk, end="", flush=True)
        print()
    else:
        print("=" * 60)
        print("RESPOSTA:")
        print("=" * 60)
        response = engine.chat(
            messages,
            max_new_tokens=args.max_tokens,
            temperature=args.temperature,
            top_k=args.top_k,
            top_p=args.top_p,
            repetition_penalty=args.repetition_penalty,
        )
        print(response)

    final_stats = engine.get_stats()
    print("=" * 60)
    print(f"Tokens gerados: {final_stats['tokens_generated']}")
    print(f"Latência média: {final_stats['avg_latency_ms']:.1f} ms")
    print(f"Throughput: {final_stats['throughput_tok_per_sec']:.1f} tok/s")
    print("=" * 60)

    engine.shutdown()


if __name__ == "__main__":
    main()
