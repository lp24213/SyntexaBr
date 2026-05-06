#!/usr/bin/env python3
"""Imprime fingerprint de bundle (manifest + assinatura) para um nome de modelo."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from vereda_ai.syntexa_core.promotion_attestation import bundle_fingerprint_for_model  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("model_name", help="Nome no registry (ex.: syntexa_small)")
    args = ap.parse_args()
    fp = bundle_fingerprint_for_model(args.model_name.strip())
    print(json.dumps(fp, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
