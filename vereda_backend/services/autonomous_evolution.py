from __future__ import annotations

import json
import subprocess
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from vereda_backend.core.config import settings

_LOCK = threading.Lock()
_THREAD: threading.Thread | None = None
_STOP = threading.Event()
_STATE: dict[str, Any] = {
    "running": False,
    "started_at": None,
    "last_run_at": None,
    "last_ok": None,
    "last_error": None,
    "last_duration_sec": None,
    "history": [],
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def _append_history(item: dict[str, Any]) -> None:
    hist = list(_STATE.get("history") or [])
    hist.append(item)
    _STATE["history"] = hist[-30:]


def _run_cmd(args: list[str], cwd: Path) -> tuple[bool, str]:
    proc = subprocess.run(
        args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    out = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    return proc.returncode == 0, out.strip()


def run_evolution_cycle_once() -> dict[str, Any]:
    root = _repo_root()
    suite = str(getattr(settings, "autonomy_evolution_benchmark_suite_path", "config/domain_benchmark_suite.jsonl"))
    report = str(getattr(settings, "autonomy_evolution_report_path", "docs/DOMAIN_BENCHMARK_REPORT.json"))
    scoreboard = str(getattr(settings, "autonomy_evolution_scoreboard_path", "config/llm_quality_scoreboard.json"))
    comparison = str(getattr(settings, "autonomy_evolution_comparison_path", "docs/LLM_FINAL_COMPARISON.md"))

    started = time.perf_counter()
    with _LOCK:
        _STATE["last_run_at"] = _now_iso()
        _STATE["last_error"] = None

    commands = [
        [
            sys.executable,
            "scripts/own-model/domain_benchmark.py",
            "--suite",
            suite,
            "--output",
            report,
            "--providers",
            "syntexa_native,future_syntexa",
            "--max-tokens",
            "512",
            "--temperature",
            "0.2",
        ],
        [
            sys.executable,
            "scripts/own-model/build_quality_scoreboard.py",
            "--input",
            report,
            "--output",
            scoreboard,
        ],
        [
            sys.executable,
            "scripts/own-model/generate_comparison_report.py",
            "--benchmark",
            report,
            "--scoreboard",
            scoreboard,
            "--output",
            comparison,
        ],
    ]
    logs: list[dict[str, Any]] = []
    ok = True
    for cmd in commands:
        cmd_ok, out = _run_cmd(cmd, root)
        logs.append({"cmd": " ".join(cmd), "ok": cmd_ok, "output_tail": out[-2000:]})
        if not cmd_ok:
            ok = False
            break
    elapsed = round(time.perf_counter() - started, 3)
    result = {
        "ok": ok,
        "ran_at": _now_iso(),
        "duration_sec": elapsed,
        "artifacts": {
            "report": report,
            "scoreboard": scoreboard,
            "comparison": comparison,
        },
        "logs": logs,
    }
    with _LOCK:
        _STATE["last_ok"] = ok
        _STATE["last_duration_sec"] = elapsed
        if not ok:
            _STATE["last_error"] = "Falha em um dos comandos da evolução autônoma."
        _append_history({"at": result["ran_at"], "ok": ok, "duration_sec": elapsed})
    return result


def _loop() -> None:
    with _LOCK:
        _STATE["running"] = True
        _STATE["started_at"] = _now_iso()
    interval = max(60, int(getattr(settings, "autonomy_evolution_interval_sec", 1800) or 1800))
    try:
        while not _STOP.is_set():
            run_evolution_cycle_once()
            if _STOP.wait(timeout=interval):
                break
    finally:
        with _LOCK:
            _STATE["running"] = False


def start_evolution_loop() -> dict[str, Any]:
    global _THREAD
    with _LOCK:
        if _THREAD and _THREAD.is_alive():
            return {"ok": True, "already_running": True, "state": dict(_STATE)}
        _STOP.clear()
        _THREAD = threading.Thread(target=_loop, name="syntexa-autonomous-evolution", daemon=True)
        _THREAD.start()
        return {"ok": True, "already_running": False, "state": dict(_STATE)}


def stop_evolution_loop() -> dict[str, Any]:
    _STOP.set()
    with _LOCK:
        return {"ok": True, "state": dict(_STATE)}


def get_evolution_status() -> dict[str, Any]:
    with _LOCK:
        return dict(_STATE)

