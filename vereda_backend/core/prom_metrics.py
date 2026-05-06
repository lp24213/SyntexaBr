from __future__ import annotations

import math
import threading
from collections import defaultdict

_LOCK = threading.Lock()
_REQ_TOTAL: dict[tuple[str, str], int] = defaultdict(int)
_ERR_TOTAL: dict[tuple[str, str], int] = defaultdict(int)
_LAT_MS_SUM: dict[str, float] = defaultdict(float)
_LAT_MS_COUNT: dict[str, int] = defaultdict(int)
_LAT_MS_BUCKETS = (50.0, 100.0, 250.0, 500.0, 1000.0, 2000.0, 5000.0, 10000.0, float("inf"))
_LAT_MS_BUCKET_COUNTS: dict[tuple[str, str], int] = defaultdict(int)
_TOKENS_SUM: dict[tuple[str, str], int] = defaultdict(int)


def record_chat_success(
    *,
    endpoint: str,
    latency_ms: float,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    total_tokens: int = 0,
) -> None:
    lat = max(0.0, float(latency_ms))
    with _LOCK:
        _REQ_TOTAL[(endpoint, "success")] += 1
        _LAT_MS_SUM[endpoint] += lat
        _LAT_MS_COUNT[endpoint] += 1
        for le in _LAT_MS_BUCKETS:
            if lat <= le:
                key = "+Inf" if le == float("inf") else f"{le:.0f}"
                _LAT_MS_BUCKET_COUNTS[(endpoint, key)] += 1
        _TOKENS_SUM[(endpoint, "prompt")] += max(0, int(prompt_tokens))
        _TOKENS_SUM[(endpoint, "completion")] += max(0, int(completion_tokens))
        _TOKENS_SUM[(endpoint, "total")] += max(0, int(total_tokens))


def record_chat_error(*, endpoint: str, error_type: str) -> None:
    e = (error_type or "unknown").strip().lower() or "unknown"
    with _LOCK:
        _REQ_TOTAL[(endpoint, "error")] += 1
        _ERR_TOTAL[(endpoint, e)] += 1


def _aggregate_latency_histogram() -> tuple[list[tuple[float, int]], int]:
    with _LOCK:
        bucket_items = list(_LAT_MS_BUCKET_COUNTS.items())
    merged: dict[float, int] = defaultdict(int)
    for (_endpoint, le), value in bucket_items:
        edge = float("inf") if le == "+Inf" else float(le)
        merged[edge] += int(value)
    ordered = sorted(merged.items(), key=lambda x: x[0])
    total = ordered[-1][1] if ordered else 0
    return ordered, total


def _histogram_quantile(q: float, buckets: list[tuple[float, int]], total: int) -> float:
    if not buckets or total <= 0:
        return 0.0
    q = max(0.0, min(1.0, float(q)))
    target = q * total
    prev_le = 0.0
    prev_count = 0
    for le, cum_count in buckets:
        if cum_count >= target:
            if math.isinf(le):
                return prev_le
            span = max(1e-9, le - prev_le)
            in_bucket = max(0.0, target - prev_count)
            bucket_count = max(1, cum_count - prev_count)
            return prev_le + (in_bucket / bucket_count) * span
        prev_le = le
        prev_count = cum_count
    return buckets[-1][0] if not math.isinf(buckets[-1][0]) else prev_le


def get_chat_slo_snapshot() -> dict[str, float]:
    with _LOCK:
        req_items = list(_REQ_TOTAL.items())
        lat_sum = float(sum(_LAT_MS_SUM.values()))
        lat_count = int(sum(_LAT_MS_COUNT.values()))
        tok_total = int(sum(v for (ep, typ), v in _TOKENS_SUM.items() if typ == "total"))
    success = sum(v for (_ep, status), v in req_items if status == "success")
    error = sum(v for (_ep, status), v in req_items if status == "error")
    total = success + error
    error_rate = (error / total) if total > 0 else 0.0
    avg_latency_ms = (lat_sum / lat_count) if lat_count > 0 else 0.0
    buckets, bucket_total = _aggregate_latency_histogram()
    p95 = _histogram_quantile(0.95, buckets, bucket_total)
    return {
        "requests_total": float(total),
        "requests_success": float(success),
        "requests_error": float(error),
        "error_rate": float(error_rate),
        "avg_latency_ms": float(avg_latency_ms),
        "p95_latency_ms": float(p95),
        "tokens_total": float(tok_total),
    }


def render_metrics_text(*, runtime_ready: int, strict_no_fallback: int, last_check_unix: float) -> str:
    lines: list[str] = [
        "# HELP syntexa_runtime_ready Own model runtime readiness (1=ready,0=not ready).",
        "# TYPE syntexa_runtime_ready gauge",
        f"syntexa_runtime_ready {int(runtime_ready)}",
        "# HELP syntexa_runtime_strict_no_fallback Strict chat mode without synthetic fallback (1=enabled).",
        "# TYPE syntexa_runtime_strict_no_fallback gauge",
        f"syntexa_runtime_strict_no_fallback {int(strict_no_fallback)}",
        "# HELP syntexa_runtime_last_check_unix Last watchdog runtime check unix timestamp.",
        "# TYPE syntexa_runtime_last_check_unix gauge",
        f"syntexa_runtime_last_check_unix {float(last_check_unix):.0f}",
        "# HELP syntexa_chat_requests_total Total chat requests by endpoint and status.",
        "# TYPE syntexa_chat_requests_total counter",
    ]
    with _LOCK:
        req_items = list(_REQ_TOTAL.items())
        err_items = list(_ERR_TOTAL.items())
        lat_sum_items = list(_LAT_MS_SUM.items())
        lat_count_items = list(_LAT_MS_COUNT.items())
        lat_bucket_items = list(_LAT_MS_BUCKET_COUNTS.items())
        tok_items = list(_TOKENS_SUM.items())
    for (endpoint, status), value in req_items:
        lines.append(
            f'syntexa_chat_requests_total{{endpoint="{endpoint}",status="{status}"}} {value}'
        )
    lines.extend(
        [
            "# HELP syntexa_chat_errors_total Total chat errors by endpoint and error type.",
            "# TYPE syntexa_chat_errors_total counter",
        ]
    )
    for (endpoint, error_type), value in err_items:
        lines.append(
            f'syntexa_chat_errors_total{{endpoint="{endpoint}",error_type="{error_type}"}} {value}'
        )
    lines.extend(
        [
            "# HELP syntexa_chat_latency_ms_sum Sum of chat latency in milliseconds.",
            "# TYPE syntexa_chat_latency_ms_sum counter",
        ]
    )
    for endpoint, value in lat_sum_items:
        lines.append(f'syntexa_chat_latency_ms_sum{{endpoint="{endpoint}"}} {value:.6f}')
    lines.extend(
        [
            "# HELP syntexa_chat_latency_ms_count Count of chat latency observations.",
            "# TYPE syntexa_chat_latency_ms_count counter",
        ]
    )
    for endpoint, value in lat_count_items:
        lines.append(f'syntexa_chat_latency_ms_count{{endpoint="{endpoint}"}} {value}')
    lines.extend(
        [
            "# HELP syntexa_chat_latency_ms Chat latency histogram in milliseconds.",
            "# TYPE syntexa_chat_latency_ms histogram",
        ]
    )
    for (endpoint, le), value in lat_bucket_items:
        lines.append(
            f'syntexa_chat_latency_ms_bucket{{endpoint="{endpoint}",le="{le}"}} {value}'
        )
    for endpoint, value in lat_sum_items:
        lines.append(f'syntexa_chat_latency_ms_sum{{endpoint="{endpoint}"}} {value:.6f}')
    for endpoint, value in lat_count_items:
        lines.append(f'syntexa_chat_latency_ms_count{{endpoint="{endpoint}"}} {value}')
    lines.extend(
        [
            "# HELP syntexa_chat_tokens_total Sum of tokens by endpoint and token type.",
            "# TYPE syntexa_chat_tokens_total counter",
        ]
    )
    for (endpoint, token_type), value in tok_items:
        lines.append(
            f'syntexa_chat_tokens_total{{endpoint="{endpoint}",token_type="{token_type}"}} {value}'
        )
    return "\n".join(lines) + "\n"
