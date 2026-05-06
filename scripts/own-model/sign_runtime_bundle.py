#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description="Gera assinatura SHA256 do bundle de runtime.")
    ap.add_argument("--bundle-dir", default="dist/own-model-bundle", help="Diretório do bundle")
    args = ap.parse_args()
    base = Path(args.bundle_dir).resolve()
    manifest = base / "manifest.json"
    tokenizer = base / "tokenizer.json"
    weights = base / "weights.pt"
    for p in (manifest, tokenizer, weights):
        if not p.is_file():
            raise SystemExit(f"Arquivo obrigatório ausente no bundle: {p}")
    payload = {
        "bundle_dir": str(base),
        "files": {
            "manifest.json": _sha256(manifest),
            "tokenizer.json": _sha256(tokenizer),
            "weights.pt": _sha256(weights),
        },
    }
    sig = base / "bundle.signature.json"
    sig.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Assinatura gerada: {sig}")


if __name__ == "__main__":
    main()
