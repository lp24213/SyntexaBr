#!/usr/bin/env python3
"""
Treino de tokenizer (SentencePiece ou BPE byte-level) — esqueleto para VM GPU / Azure.
Instalar dependências no ambiente de treino: pip install sentencepiece (opcional).
"""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description="Treinar tokenizer proprietário")
    ap.add_argument("--corpus", required=True, help="JSONL com campo 'text' (saída de prepare_ptbr_data.py)")
    ap.add_argument("--out-dir", default="checkpoints/tokenizer", help="Diretório de saída")
    ap.add_argument("--vocab-size", type=int, default=32000)
    args = ap.parse_args()
    corpus = Path(args.corpus)
    if not corpus.is_file():
        raise SystemExit(f"Corpus não encontrado: {corpus}")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    # Integração real: import sentencepiece as spm; spm.SentencePieceTrainer.train(...)
    (out_dir / "README.txt").write_text(
        "Substituir por SentencePiece.train com input_sentence_size e model_type=BPE.\n",
        encoding="utf-8",
    )
    print(f"Placeholder OK — configure SentencePiece e aponte --corpus {corpus}")
    print(f"Saída esperada: {out_dir / 'syntexa.tiktoken.model'} (ou .model)")


if __name__ == "__main__":
    main()
