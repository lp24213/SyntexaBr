#!/usr/bin/env python3
from __future__ import annotations

import argparse


def main() -> None:
    ap = argparse.ArgumentParser(description="Gera preset de ambiente para desempenho da IA própria na VM")
    ap.add_argument("--profile", choices=["balanced", "quality", "throughput"], default="quality")
    args = ap.parse_args()

    if args.profile == "throughput":
        out = {
            "OWN_MODEL_MAX_NEW_TOKENS": "512",
            "OWN_MODEL_TEMPERATURE": "0.7",
            "OWN_MODEL_TOP_K": "50",
            "LLM_MAX_CONCURRENCY": "64",
            "CHAT_MAX_MODEL_TOKENS": "8192",
        }
    elif args.profile == "balanced":
        out = {
            "OWN_MODEL_MAX_NEW_TOKENS": "768",
            "OWN_MODEL_TEMPERATURE": "0.75",
            "OWN_MODEL_TOP_K": "64",
            "LLM_MAX_CONCURRENCY": "48",
            "CHAT_MAX_MODEL_TOKENS": "8192",
        }
    else:
        out = {
            "OWN_MODEL_MAX_NEW_TOKENS": "1536",
            "OWN_MODEL_TEMPERATURE": "0.85",
            "OWN_MODEL_TOP_K": "96",
            "LLM_MAX_CONCURRENCY": "32",
            "CHAT_MAX_MODEL_TOKENS": "12288",
        }

    print("# Adicione no .env")
    for k, v in out.items():
        print(f"{k}={v}")


if __name__ == "__main__":
    main()
