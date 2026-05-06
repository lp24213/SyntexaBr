#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str], cwd: Path) -> dict:
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    output = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    return {"cmd": " ".join(cmd), "ok": proc.returncode == 0, "output_tail": output[-3000:]}


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    steps = [
        [sys.executable, "scripts/own-model/verify_no_fallback.py"],
        [
            sys.executable,
            "scripts/own-model/domain_benchmark.py",
            "--suite",
            "config/domain_benchmark_suite.jsonl",
            "--providers",
            "syntexa_native,future_syntexa",
            "--output",
            "docs/DOMAIN_BENCHMARK_REPORT.json",
        ],
        [
            sys.executable,
            "scripts/own-model/build_quality_scoreboard.py",
            "--input",
            "docs/DOMAIN_BENCHMARK_REPORT.json",
            "--output",
            "config/llm_quality_scoreboard.json",
        ],
        [
            sys.executable,
            "scripts/own-model/generate_comparison_report.py",
            "--benchmark",
            "docs/DOMAIN_BENCHMARK_REPORT.json",
            "--scoreboard",
            "config/llm_quality_scoreboard.json",
            "--output",
            "docs/LLM_FINAL_COMPARISON.md",
        ],
    ]
    results = []
    ok = True
    for step in steps:
        row = _run(step, root)
        results.append(row)
        if not row["ok"]:
            ok = False
            break
    payload = {
        "ok": ok,
        "steps": results,
        "artifacts": {
            "benchmark_report": "docs/DOMAIN_BENCHMARK_REPORT.json",
            "scoreboard": "config/llm_quality_scoreboard.json",
            "comparison_report": "docs/LLM_FINAL_COMPARISON.md",
        },
    }
    print(json.dumps(payload, ensure_ascii=True))
    raise SystemExit(0 if ok else 2)


if __name__ == "__main__":
    main()
