#!/usr/bin/env python3
"""
Executa um conjunto de prompts contra /v1/chat/completions (JSONL: uma linha JSON por prompt).
Saída: JSONL com latência_ms e pré-visualização da resposta.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", type=Path, required=True, help="Ficheiro .jsonl com {\"prompt\": \"...\"}")
    ap.add_argument("--base-url", default="http://127.0.0.1:8000")
    ap.add_argument("--token", default="")
    ap.add_argument("--model", default="vereda-small-echo")
    ap.add_argument("--max-tokens", type=int, default=256)
    ap.add_argument("--timeout", type=float, default=180.0)
    args = ap.parse_args()
    url = args.base_url.rstrip("/") + "/v1/chat/completions"
    lines = args.suite.read_text(encoding="utf-8").strip().splitlines()
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        row = json.loads(line)
        prompt = str(row.get("prompt") or row.get("content") or "")
        body = json.dumps(
            {
                "model": args.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": args.max_tokens,
                "stream": False,
            }
        ).encode("utf-8")
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        if args.token.strip():
            req.add_header("Authorization", f"Bearer {args.token.strip()}")
        t0 = time.perf_counter()
        try:
            with urllib.request.urlopen(req, timeout=args.timeout) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
            data = json.loads(raw)
            choice = (data.get("choices") or [{}])[0]
            msg = (choice.get("message") or {}).get("content") or ""
            out = {
                "i": i,
                "ok": True,
                "latency_ms": round((time.perf_counter() - t0) * 1000, 2),
                "reply_preview": (msg or "")[:400],
            }
        except Exception as exc:
            out = {"i": i, "ok": False, "error": str(exc)[:500]}
        print(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
