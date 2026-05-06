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
    ap = argparse.ArgumentParser(description="Valida assinatura SHA256 do bundle de runtime.")
    ap.add_argument("--bundle-dir", default="dist/own-model-bundle", help="Diretório do bundle")
    args = ap.parse_args()
    base = Path(args.bundle_dir).resolve()
    sig_path = base / "bundle.signature.json"
    if not sig_path.is_file():
        raise SystemExit(f"Assinatura ausente: {sig_path}")
    sig = json.loads(sig_path.read_text(encoding="utf-8"))
    files = sig.get("files") or {}
    for name, expected in files.items():
        p = base / str(name)
        if not p.is_file():
            raise SystemExit(f"Arquivo ausente para verificação: {p}")
        actual = _sha256(p)
        if actual != str(expected):
            raise SystemExit(f"Checksum inválido em {name}: expected={expected} actual={actual}")
    print("Bundle verificado com sucesso.")


if __name__ == "__main__":
    main()
