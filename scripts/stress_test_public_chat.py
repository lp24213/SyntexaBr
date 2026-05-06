import argparse
import json
import statistics
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import requests


HARD_PROMPTS = [
    "Explain SAT NP-complete with a formal reduction sketch from 3-SAT to CLIQUE.",
    "Compute integral of x^2*exp(-x) and verify by differentiation.",
    "Design collaborative spreadsheet architecture with conflict resolution and cell-level ACLs.",
    "Compare transformer, RNN, and state-space models for long-context time series forecasting.",
    "Propose a PostgreSQL multi-tenant schema with audit logging and LGPD-compliant data erasure.",
    "Write a robust incident response plan for API outage with SLO, rollback, and comms timeline.",
    "Explain Byzantine fault tolerance vs Raft and practical trade-offs in cloud deployments.",
    "Create a performance plan to reduce API p95 latency from 2.4s to under 900ms.",
    "Derive the closed-form solution of a first-order linear ODE and validate conditions.",
    "Design a secure file export pipeline (PDF/XLSX/DOCX) with queueing, retries, and tracing.",
]


@dataclass
class Result:
    index: int
    status_code: int
    latency_sec: float
    ok: bool
    answer_len: int
    answer_preview: str
    error: str


def run_once(url: str, prompt: str, timeout: int, max_tokens: int) -> Result:
    started = time.perf_counter()
    try:
        response = requests.post(
            url,
            json={
                "model": "syntexa",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
                "max_tokens": max_tokens,
            },
            timeout=timeout,
        )
        latency = time.perf_counter() - started
    except Exception as exc:
        return Result(
            index=-1,
            status_code=0,
            latency_sec=time.perf_counter() - started,
            ok=False,
            answer_len=0,
            answer_preview="",
            error=str(exc),
        )

    if response.status_code != 200:
        return Result(
            index=-1,
            status_code=response.status_code,
            latency_sec=latency,
            ok=False,
            answer_len=0,
            answer_preview="",
            error=(response.text or "")[:300],
        )

    try:
        body = response.json()
        answer = (
            ((body.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
        )
    except Exception as exc:
        return Result(
            index=-1,
            status_code=response.status_code,
            latency_sec=latency,
            ok=False,
            answer_len=0,
            answer_preview="",
            error=f"JSON parse error: {exc}",
        )

    ok = bool(answer.strip())
    return Result(
        index=-1,
        status_code=response.status_code,
        latency_sec=latency,
        ok=ok,
        answer_len=len(answer),
        answer_preview=answer[:220].replace("\n", " "),
        error="" if ok else "empty answer",
    )


def summarize(results: list[Result]) -> dict:
    total = len(results)
    success = [r for r in results if r.ok]
    failed = [r for r in results if not r.ok]
    latencies = [r.latency_sec for r in results]
    p50 = statistics.median(latencies) if latencies else 0.0
    p95 = (
        sorted(latencies)[max(0, min(len(latencies) - 1, int(0.95 * len(latencies)) - 1))]
        if latencies
        else 0.0
    )
    return {
        "total": total,
        "success": len(success),
        "failed": len(failed),
        "success_rate": (len(success) / total * 100.0) if total else 0.0,
        "latency_avg_sec": (sum(latencies) / total) if total else 0.0,
        "latency_p50_sec": p50,
        "latency_p95_sec": p95,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Stress test public Syntexa chat endpoint.")
    parser.add_argument("--url", default="https://syntexabr.com.br/v1/public-chat")
    parser.add_argument("--rounds", type=int, default=30)
    parser.add_argument("--timeout", type=int, default=120)
    parser.add_argument("--max-tokens", type=int, default=900)
    parser.add_argument(
        "--output",
        default="docs/STRESS_TEST_REPORT.json",
        help="Path to JSON report file.",
    )
    args = parser.parse_args()

    results: list[Result] = []
    for i in range(args.rounds):
        prompt = HARD_PROMPTS[i % len(HARD_PROMPTS)]
        res = run_once(args.url, prompt, args.timeout, args.max_tokens)
        res.index = i + 1
        results.append(res)
        state = "OK" if res.ok else "FAIL"
        print(
            f"[{i + 1:02d}/{args.rounds}] {state} status={res.status_code} "
            f"lat={res.latency_sec:.2f}s len={res.answer_len} err={res.error[:80]}"
        )

    summary = summarize(results)
    payload = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "url": args.url,
        "rounds": args.rounds,
        "summary": summary,
        "results": [r.__dict__ for r in results],
    }

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== SUMMARY ===")
    for k, v in summary.items():
        if isinstance(v, float):
            print(f"{k}: {v:.4f}")
        else:
            print(f"{k}: {v}")
    print(f"report_file: {out_path}")
    return 0 if summary["failed"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
