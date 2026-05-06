#!/usr/bin/env python3
"""Percorre config/*.manifest.json e checkpoints/*/manifest.json e valida."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
TOOL = _ROOT / "scripts" / "own-model" / "validate_model_manifest.py"


def main() -> None:
    patterns = [
        _ROOT / "config",
        _ROOT / "checkpoints",
    ]
    files: list[Path] = []
    for base in patterns:
        if not base.is_dir():
            continue
        if base.name == "config":
            files.extend(base.glob("*.manifest.json"))
        else:
            files.extend(base.glob("*/manifest.json"))
    files = sorted(set(files))
    if not files:
        print("Nenhum manifest encontrado; exit 0")
        raise SystemExit(0)
    failed = 0
    for p in files:
        r = subprocess.run([sys.executable, str(TOOL), str(p)], capture_output=True, text=True)
        if r.returncode != 0:
            failed += 1
            print(p, file=sys.stderr)
            print(r.stderr or r.stdout, file=sys.stderr)
    if failed:
        print(f"Falharam {failed}/{len(files)}", file=sys.stderr)
        raise SystemExit(1)
    print(f"OK {len(files)} manifest(s)")


if __name__ == "__main__":
    main()
