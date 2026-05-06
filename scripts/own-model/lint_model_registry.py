#!/usr/bin/env python3
"""Valida syntexa_model_registry.json: active existe na lista, entradas mínimas."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "registry",
        type=Path,
        nargs="?",
        default=None,
        help="Caminho ao registry JSON (default: config/syntexa_model_registry.json)",
    )
    args = ap.parse_args()
    root = Path(__file__).resolve().parents[2]
    path = args.registry or (root / "config" / "syntexa_model_registry.json")
    if not path.is_file():
        print(f"Registry ausente (skip opcional em CI): {path}", file=sys.stderr)
        raise SystemExit(0)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        print(f"JSON inválido: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
    active = str(data.get("active") or "").strip()
    models = data.get("models") or []
    if not active:
        print("Campo 'active' vazio", file=sys.stderr)
        raise SystemExit(1)
    names: list[str] = []
    for i, m in enumerate(models):
        if not isinstance(m, dict):
            print(f"models[{i}] não é objecto", file=sys.stderr)
            raise SystemExit(1)
        n = str(m.get("name", "")).strip()
        if not n:
            print(f"models[{i}] sem name", file=sys.stderr)
            raise SystemExit(1)
        names.append(n)
    if active not in names:
        print(f"active='{active}' não está em models: {names}", file=sys.stderr)
        raise SystemExit(1)
    print(json.dumps({"ok": True, "path": str(path), "active": active, "models_count": len(names)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
