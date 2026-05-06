#!/usr/bin/env python3
"""Junta vários JSON de snapshot (readiness/slo/policy) num único relatório."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", type=Path, help="Ficheiros .json")
    ap.add_argument("-o", "--output", type=Path, default=None)
    args = ap.parse_args()
    merged: dict = {"sources": [], "parts": {}}
    for p in args.files:
        if not p.is_file():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        key = p.stem.split("-")[0] if "-" in p.stem else p.stem
        merged["parts"][key] = data
        merged["sources"].append(str(p))
    out = json.dumps(merged, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(out, encoding="utf-8")
    else:
        print(out)


if __name__ == "__main__":
    main()
