#!/usr/bin/env python3
from __future__ import annotations

import argparse
import statistics
import time
from pathlib import Path
import sys

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    import torch
except Exception:
    raise SystemExit("Torch não instalado. Use: pip install -r requirements-research.txt")

from training.model_syntexa import SyntexaConfig, SyntexaDecoderLM
from vereda_ai.syntexa_core.model_manifest import ModelManifest
from vereda_ai.syntexa_core.tokenizer import SyntexaTokenizer


def main() -> None:
    ap = argparse.ArgumentParser(description="Benchmark da IA própria Syntexa (latência e tokens/s)")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--prompt", default="Explique um plano estratégico de crescimento para PME.")
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--max-new-tokens", type=int, default=512)
    ap.add_argument("--temperature", type=float, default=0.8)
    ap.add_argument("--top-k", type=int, default=80)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    device = args.device
    if device.startswith("cuda") and not torch.cuda.is_available():
        device = "cpu"

    mf = ModelManifest.from_file(args.manifest)
    tok = SyntexaTokenizer.load(mf.tokenizer_path)
    payload = torch.load(mf.checkpoint_path, map_location=device)
    cfg = SyntexaConfig(**(payload.get("config") or {}))
    model = SyntexaDecoderLM(cfg).to(device)
    model.load_state_dict(payload["model_state"], strict=True)
    model.eval()

    prompt = f"USER: {args.prompt}\nASSISTANT:"
    input_ids = tok.encode(prompt, add_special_tokens=True, max_length=max(16, cfg.max_seq_len))

    lat_ms = []
    tps = []
    for i in range(max(1, args.runs)):
        if device.startswith("cuda"):
            torch.cuda.synchronize()
        t0 = time.perf_counter()
        with torch.no_grad():
            out = model.generate(
                input_ids,
                max_new_tokens=max(8, int(args.max_new_tokens)),
                temperature=float(args.temperature),
                top_k=max(1, int(args.top_k)),
                eos_id=tok.eos_id,
                device=device,
            )
        if device.startswith("cuda"):
            torch.cuda.synchronize()
        dt = (time.perf_counter() - t0) * 1000.0
        new_tokens = max(1, len(out) - len(input_ids))
        lat_ms.append(dt)
        tps.append(new_tokens / max(1e-6, dt / 1000.0))
        print(f"run={i+1} latency_ms={dt:.2f} new_tokens={new_tokens} tok_per_sec={tps[-1]:.2f}")

    print("----")
    print(f"model={mf.name} device={device} runs={len(lat_ms)}")
    print(f"latency_avg_ms={statistics.mean(lat_ms):.2f} latency_p95_ms={sorted(lat_ms)[int(0.95*(len(lat_ms)-1))]:.2f}")
    print(f"tok_per_sec_avg={statistics.mean(tps):.2f} tok_per_sec_max={max(tps):.2f}")


if __name__ == "__main__":
    main()
