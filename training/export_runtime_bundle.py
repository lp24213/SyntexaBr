#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from vereda_ai.syntexa_core.model_manifest import ModelManifest


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description="Empacota bundle de runtime do modelo próprio")
    ap.add_argument("--manifest", required=True, help="manifest.json do modelo")
    ap.add_argument("--out-dir", default="dist/own-model-bundle", help="Diretório de saída")
    ap.add_argument("--sign", action="store_true", help="Gera bundle.signature.json com SHA256 dos artefatos")
    args = ap.parse_args()

    mf_path = Path(args.manifest).resolve()
    mf = ModelManifest.from_file(mf_path)
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    tok_src = Path(mf.tokenizer_path).resolve()
    w_src = Path(mf.checkpoint_path).resolve()
    mf_dst = out / "manifest.json"
    tok_dst = out / "tokenizer.json"
    w_dst = out / "weights.pt"

    shutil.copy2(tok_src, tok_dst)
    shutil.copy2(w_src, w_dst)

    rebased = {
        "name": mf.name,
        "family": mf.family,
        "stage": mf.stage,
        "vocab_size": mf.vocab_size,
        "hidden_size": mf.hidden_size,
        "num_layers": mf.num_layers,
        "num_heads": mf.num_heads,
        "max_seq_len": mf.max_seq_len,
        "checkpoint_path": str(w_dst),
        "tokenizer_path": str(tok_dst),
        "metadata": mf.metadata,
    }
    mf_dst.write_text(json.dumps(rebased, ensure_ascii=False, indent=2), encoding="utf-8")
    if args.sign:
        sig_payload = {
            "bundle_dir": str(out),
            "files": {
                "manifest.json": _sha256(mf_dst),
                "tokenizer.json": _sha256(tok_dst),
                "weights.pt": _sha256(w_dst),
            },
        }
        (out / "bundle.signature.json").write_text(
            json.dumps(sig_payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    print(f"Bundle exportado em: {out}")


if __name__ == "__main__":
    main()
