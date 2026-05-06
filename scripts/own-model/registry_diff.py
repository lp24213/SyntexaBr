#!/usr/bin/env python3
"""Compara dois ficheiros de registry JSON (active + lista de nomes)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _load(p: Path) -> dict:
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("before", type=Path)
    ap.add_argument("after", type=Path)
    args = ap.parse_args()
    a, b = _load(args.before), _load(args.after)
    names_a = {str(m.get("name")) for m in (a.get("models") or []) if isinstance(m, dict)}
    names_b = {str(m.get("name")) for m in (b.get("models") or []) if isinstance(m, dict)}
    print(
        json.dumps(
            {
                "active_before": a.get("active"),
                "active_after": b.get("active"),
                "models_added": sorted(names_b - names_a),
                "models_removed": sorted(names_a - names_b),
                "same_active": a.get("active") == b.get("active"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
