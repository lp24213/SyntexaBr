#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time


def _fmt_pct(x: float) -> str:
    return f"{x * 100.0:.1f}%"


def main() -> None:
    ap = argparse.ArgumentParser(description="Gera relatório final comparativo por domínio/modelo.")
    ap.add_argument("--benchmark", type=Path, default=Path("docs/DOMAIN_BENCHMARK_REPORT.json"))
    ap.add_argument("--scoreboard", type=Path, default=Path("config/llm_quality_scoreboard.json"))
    ap.add_argument("--output", type=Path, default=Path("docs/LLM_FINAL_COMPARISON.md"))
    ap.add_argument(
        "--external-baselines",
        type=Path,
        default=None,
        help="Opcional JSON com benchmarks externos (GPT/Claude/Gemini) no mesmo formato agregado.",
    )
    args = ap.parse_args()

    bench = json.loads(args.benchmark.read_text(encoding="utf-8"))
    board = json.loads(args.scoreboard.read_text(encoding="utf-8"))
    ext = {}
    if args.external_baselines and args.external_baselines.exists():
        ext = json.loads(args.external_baselines.read_text(encoding="utf-8"))

    lines: list[str] = []
    lines.append("# Relatório Final Comparativo de Modelos")
    lines.append("")
    lines.append(f"- Gerado em: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
    lines.append(f"- Fonte benchmark: `{args.benchmark}`")
    lines.append(f"- Fonte scoreboard: `{args.scoreboard}`")
    lines.append("")
    lines.append("## Placar por provedor")
    lines.append("")
    for provider, row in sorted((board.get("providers") or {}).items()):
        gs = float(row.get("global_score") or 0.0)
        lat = float(row.get("avg_latency_ms") or 0.0)
        sample = int(row.get("sample_size") or 0)
        lines.append(f"- **{provider}**: score global `{gs:.3f}`, latência média `{lat:.2f} ms`, amostras `{sample}`")
    lines.append("")
    lines.append("## Vencedor por domínio")
    lines.append("")
    domains: dict[str, list[tuple[str, float]]] = {}
    for provider, row in (board.get("providers") or {}).items():
        for domain, score in (row.get("domains") or {}).items():
            domains.setdefault(domain, []).append((provider, float(score)))
    for domain, scores in sorted(domains.items()):
        scores.sort(key=lambda x: x[1], reverse=True)
        best = scores[0]
        lines.append(f"- `{domain}`: melhor provedor atual = **{best[0]}** (`{best[1]:.3f}`)")
    lines.append("")
    lines.append("## Comparação com baselines externos")
    lines.append("")
    if ext:
        for model_name, stats in sorted(ext.items()):
            q = float(stats.get("avg_quality") or 0.0)
            s = float(stats.get("success_rate") or 0.0)
            l = float(stats.get("avg_latency_ms") or 0.0)
            lines.append(
                f"- **{model_name}**: qualidade `{q:.3f}`, sucesso `{_fmt_pct(s)}`, latência média `{l:.2f} ms`"
            )
    else:
        lines.append("- Baselines externos não informados neste run.")
        lines.append("- Para comparar com GPT/Claude/Gemini, passe `--external-baselines <arquivo.json>`.")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(args.output)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
