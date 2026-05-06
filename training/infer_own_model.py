#!/usr/bin/env python3
from __future__ import annotations

import argparse
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
    ap = argparse.ArgumentParser(description="Inferência local direta do modelo próprio Syntexa")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--max-new-tokens", type=int, default=1024)
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
    with torch.no_grad():
        out_ids = model.generate(
            input_ids,
            max_new_tokens=max(32, int(args.max_new_tokens)),
            temperature=float(args.temperature),
            top_k=max(1, int(args.top_k)),
            eos_id=tok.eos_id,
            device=device,
        )
    text = tok.decode(out_ids[len(input_ids) :]).strip()
    print(text or "[empty completion]")


if __name__ == "__main__":
    main()
