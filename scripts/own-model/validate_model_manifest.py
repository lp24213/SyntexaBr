#!/usr/bin/env python3
"""Valida ficheiro manifest do modelo (schema + existência de tokenizer; checkpoint opcional)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from vereda_ai.syntexa_core.model_manifest import ModelManifest  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("manifest", type=Path, help="Caminho para manifest.json")
    ap.add_argument(
        "--require-checkpoint",
        action="store_true",
        help="Falha se checkpoint_path não existir como ficheiro",
    )
    args = ap.parse_args()
    p = args.manifest.resolve()
    if not p.is_file():
        print(f"Manifest ausente: {p}", file=sys.stderr)
        raise SystemExit(2)
    try:
        m = ModelManifest.from_file(p)
    except (json.JSONDecodeError, OSError, TypeError, ValueError) as exc:
        print(f"Manifest inválido: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    issues: list[str] = []
    tok = Path(m.tokenizer_path)
    if not tok.is_file():
        issues.append(f"tokenizer não encontrado: {m.tokenizer_path}")
    ck = Path(m.checkpoint_path)
    if args.require_checkpoint and not ck.is_file():
        issues.append(f"checkpoint não encontrado: {m.checkpoint_path}")
    if issues:
        for i in issues:
            print(i, file=sys.stderr)
        raise SystemExit(1)
    print(json.dumps({"ok": True, "name": m.name, "stage": m.stage, "manifest": str(p)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
