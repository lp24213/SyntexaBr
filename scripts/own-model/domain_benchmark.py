#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
import time
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from vereda_ai.ai import LLMEngine  # noqa: E402


def _heuristic_quality(reply: str, expected_keywords: list[str]) -> float:
    text = (reply or "").strip().lower()
    if not text:
        return 0.0
    kw_hits = 0
    for kw in expected_keywords:
        k = str(kw or "").strip().lower()
        if k and k in text:
            kw_hits += 1
    kw_score = kw_hits / max(1, len(expected_keywords))
    len_score = min(1.0, len(text) / 480.0)
    return max(0.0, min(1.0, kw_score * 0.7 + len_score * 0.3))


def main() -> None:
    ap = argparse.ArgumentParser(description="Benchmark automático por domínio/provedor.")
    ap.add_argument(
        "--suite",
        type=Path,
        default=Path("config/domain_benchmark_suite.jsonl"),
        help="JSONL com: domain, prompt, expected_keywords[]",
    )
    ap.add_argument(
        "--providers",
        default="",
        help="Lista separada por vírgula. Vazio = todos os provedores disponíveis.",
    )
    ap.add_argument(
        "--output",
        type=Path,
        default=Path("docs/DOMAIN_BENCHMARK_REPORT.json"),
        help="Relatório JSON de saída.",
    )
    ap.add_argument("--max-tokens", type=int, default=512)
    ap.add_argument("--temperature", type=float, default=0.2)
    args = ap.parse_args()

    engine = LLMEngine()
    providers = [p.strip() for p in args.providers.split(",") if p.strip()]
    if not providers:
        providers = [p for p in engine.available_providers() if p != "dummy"]
    rows = []
    for line in args.suite.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s:
            continue
        rows.append(json.loads(s))
    out_rows: list[dict] = []
    grouped: dict[tuple[str, str], list[dict]] = {}
    for row in rows:
        domain = str(row.get("domain") or "geral").strip().lower()
        prompt = str(row.get("prompt") or "").strip()
        expected = [str(x) for x in (row.get("expected_keywords") or [])]
        for provider in providers:
            started = time.perf_counter()
            ok = True
            err = ""
            reply = ""
            try:
                reply = engine.chat(
                    [{"role": "user", "content": prompt}],
                    provider=provider,
                    temperature=args.temperature,
                    max_tokens=args.max_tokens,
                    domain=domain,
                )
            except Exception as exc:
                ok = False
                err = str(exc)
            latency_ms = round((time.perf_counter() - started) * 1000.0, 2)
            quality = _heuristic_quality(reply, expected) if ok else 0.0
            item = {
                "provider": provider,
                "domain": domain,
                "prompt": prompt,
                "ok": ok,
                "latency_ms": latency_ms,
                "quality": round(quality, 4),
                "error": err[:500],
                "reply_preview": (reply or "")[:500],
            }
            out_rows.append(item)
            grouped.setdefault((provider, domain), []).append(item)

    summary = {}
    for (provider, domain), items in grouped.items():
        oks = [1 if i["ok"] else 0 for i in items]
        lat = [float(i["latency_ms"]) for i in items]
        qual = [float(i["quality"]) for i in items]
        summary.setdefault(provider, {})
        summary[provider][domain] = {
            "count": len(items),
            "success_rate": round(sum(oks) / max(1, len(oks)), 4),
            "avg_latency_ms": round(statistics.fmean(lat), 2),
            "avg_quality": round(statistics.fmean(qual), 4),
        }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": int(time.time()),
        "suite": str(args.suite),
        "providers": providers,
        "summary": summary,
        "results": out_rows,
    }
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(args.output), "providers": providers}, ensure_ascii=False))


if __name__ == "__main__":
    main()
