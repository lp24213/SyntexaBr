#!/usr/bin/env python3
"""Um único POST /v1/chat/completions para smoke de gateway (timeout configurável)."""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8000", help="Origem da API")
    ap.add_argument("--token", default="", help="Bearer opcional")
    ap.add_argument("--model", default="vereda-small-echo")
    ap.add_argument("--message", default="Responda só: OK")
    ap.add_argument("--max-tokens", type=int, default=32)
    ap.add_argument("--timeout", type=float, default=120.0)
    args = ap.parse_args()
    url = args.base_url.rstrip("/") + "/v1/chat/completions"
    body = {
        "model": args.model,
        "messages": [{"role": "user", "content": args.message}],
        "max_tokens": args.max_tokens,
        "stream": False,
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    if args.token.strip():
        req.add_header("Authorization", f"Bearer {args.token.strip()}")
    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        print(exc.read().decode("utf-8", errors="replace")[:2000], file=sys.stderr)
        raise SystemExit(1) from exc
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from exc
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        print(raw[:2000])
        raise SystemExit(1)
    choice = (obj.get("choices") or [{}])[0]
    msg = (choice.get("message") or {}).get("content") or ""
    print(json.dumps({"ok": True, "reply_preview": (msg or "")[:500], "id": obj.get("id")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
