#!/usr/bin/env python3
"""
Normaliza corpus PT-BR (txt/jsonl) para treino — sem baixar modelos de terceiros.
Saída: datasets/syntexa_corpus.jsonl (uma linha JSON por amostra: {"text": "..."})
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def clean_block(text: str) -> str:
    t = text.replace("\r\n", "\n").strip()
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t


def main() -> None:
    p = argparse.ArgumentParser(description="Preparar dados PT-BR para treino Syntexa")
    p.add_argument("inputs", nargs="+", help="Ficheiros .txt ou .jsonl (campo 'text')")
    p.add_argument("-o", "--output", default="datasets/syntexa_corpus.jsonl", help="JSONL de saída")
    args = p.parse_args()
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    n = 0
    with out.open("w", encoding="utf-8") as fout:
        for path_str in args.inputs:
            path = Path(path_str)
            if not path.is_file():
                continue
            if path.suffix.lower() == ".jsonl":
                for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        text = clean_block(str(obj.get("text", "")))
                    except json.JSONDecodeError:
                        continue
                    if len(text) < 20:
                        continue
                    fout.write(json.dumps({"text": text}, ensure_ascii=False) + "\n")
                    n += 1
            else:
                raw = clean_block(path.read_text(encoding="utf-8", errors="ignore"))
                if len(raw) < 20:
                    continue
                fout.write(json.dumps({"text": raw}, ensure_ascii=False) + "\n")
                n += 1
    print(f"OK: {n} amostras -> {out.resolve()}")


if __name__ == "__main__":
    main()
