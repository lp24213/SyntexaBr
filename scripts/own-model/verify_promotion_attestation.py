#!/usr/bin/env python3
"""CLI: valida JSON de atestação (ficheiro ou stdin) sem subir API."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from vereda_ai.syntexa_core.promotion_attestation import verify_attestation_document  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Verifica attestation_sha256 de um documento de promoção.")
    ap.add_argument(
        "path",
        nargs="?",
        help="Ficheiro JSON (omitir para ler stdin)",
    )
    args = ap.parse_args()
    raw = Path(args.path).read_text(encoding="utf-8") if args.path else sys.stdin.read()
    try:
        doc = json.loads(raw or "{}")
    except json.JSONDecodeError as exc:
        print(json.dumps({"valid": False, "detail": str(exc), "recomputed_sha256": None}, ensure_ascii=False))
        raise SystemExit(2) from exc
    if not isinstance(doc, dict):
        print("JSON inválido: raiz tem de ser objecto.", file=sys.stderr)
        raise SystemExit(2)
    ok, msg, recomputed = verify_attestation_document(doc)
    print(json.dumps({"valid": ok, "detail": msg, "recomputed_sha256": recomputed}, ensure_ascii=False))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
