#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys

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
from vereda_ai.syntexa_core.model_manifest import ModelManifest
from vereda_ai.syntexa_core.tokenizer import SyntexaTokenizer


def _load_eval_texts(path: Path) -> list[str]:
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
        if len(text) > 20:
            out.append(text)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Avaliação básica do modelo Syntexa próprio")
    ap.add_argument("--manifest", required=True, help="manifest.json gerado no checkpoint")
    ap.add_argument("--data", required=True, help="JSONL de validação com campo text")
    ap.add_argument("--max-samples", type=int, default=200)
    ap.add_argument("--device", default="cuda")
    args = ap.parse_args()

    if torch is None or F is None:
        raise SystemExit("Torch não encontrado. Instale torch para avaliação.")

    device = args.device
    if device.startswith("cuda") and not torch.cuda.is_available():
        device = "cpu"

    mf = ModelManifest.from_file(args.manifest)
    tok = SyntexaTokenizer.load(mf.tokenizer_path)
    ckpt = torch.load(mf.checkpoint_path, map_location=device)
    cfg = SyntexaConfig(**ckpt.get("config", {}))
    model = SyntexaDecoderLM(cfg).to(device)
    model.load_state_dict(ckpt["model_state"], strict=True)
    model.eval()

    texts = _load_eval_texts(Path(args.data))[: max(1, args.max_samples)]
    if not texts:
        raise SystemExit("Dataset de avaliação vazio.")

    losses = []
    with torch.no_grad():
        for t in texts:
            ids = tok.encode(t, add_special_tokens=True, max_length=cfg.max_seq_len)
            if len(ids) < 3:
                continue
            x = torch.tensor([ids[:-1]], dtype=torch.long, device=device)
            y = torch.tensor([ids[1:]], dtype=torch.long, device=device)
            logits = model(x)
            loss = F.cross_entropy(logits.reshape(-1, logits.size(-1)), y.reshape(-1))
            losses.append(float(loss.item()))

    if not losses:
        raise SystemExit("Sem amostras válidas para calcular loss.")
    avg = sum(losses) / len(losses)
    ppl = math.exp(min(20.0, avg))
    print(f"model={mf.name} samples={len(losses)} avg_loss={avg:.4f} perplexity={ppl:.2f}")


if __name__ == "__main__":
    main()
