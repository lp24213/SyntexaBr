#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import time


def main() -> None:
    ap = argparse.ArgumentParser(description="Gera placar de qualidade por provedor/domínio.")
    ap.add_argument(
        "--input",
        type=Path,
        default=Path("docs/DOMAIN_BENCHMARK_REPORT.json"),
    )
    ap.add_argument(
        "--output",
        type=Path,
        default=Path("config/llm_quality_scoreboard.json"),
    )
    args = ap.parse_args()

    data = json.loads(args.input.read_text(encoding="utf-8"))
    results = data.get("results") or []
    by_provider_domain: dict[tuple[str, str], list[dict]] = {}
    by_provider_global: dict[str, list[dict]] = {}
    for row in results:
        p = str(row.get("provider") or "").strip()
        d = str(row.get("domain") or "geral").strip().lower()
        if not p:
            continue
        by_provider_domain.setdefault((p, d), []).append(row)
        by_provider_global.setdefault(p, []).append(row)

    out_providers: dict[str, dict] = {}
    for provider, rows in by_provider_global.items():
        domains: dict[str, float] = {}
        for (p, d), dr in by_provider_domain.items():
            if p != provider:
                continue
            sr = statistics.fmean(1.0 if bool(x.get("ok")) else 0.0 for x in dr)
            q = statistics.fmean(float(x.get("quality") or 0.0) for x in dr)
            lat = statistics.fmean(float(x.get("latency_ms") or 0.0) for x in dr)
            latency_bonus = max(0.0, min(1.0, 1.0 - (lat / 15000.0)))
            score = 0.5 * q + 0.35 * sr + 0.15 * latency_bonus
            domains[d] = round(max(0.0, min(1.0, score)), 4)

        global_sr = statistics.fmean(1.0 if bool(x.get("ok")) else 0.0 for x in rows)
        global_q = statistics.fmean(float(x.get("quality") or 0.0) for x in rows)
        global_lat = statistics.fmean(float(x.get("latency_ms") or 0.0) for x in rows)
        global_bonus = max(0.0, min(1.0, 1.0 - (global_lat / 15000.0)))
        global_score = 0.5 * global_q + 0.35 * global_sr + 0.15 * global_bonus

        out_providers[provider] = {
            "global_score": round(max(0.0, min(1.0, global_score)), 4),
            "avg_latency_ms": round(global_lat, 2),
            "domains": domains,
            "sample_size": len(rows),
        }

    payload = {
        "generated_at": int(time.time()),
        "source_report": str(args.input),
        "providers": out_providers,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(args.output), "providers": sorted(out_providers.keys())}, ensure_ascii=False))


if __name__ == "__main__":
    main()
