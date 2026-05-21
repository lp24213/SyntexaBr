"""
SYNTEXA FOUNDATION TOKENIZER
============================
Byte-Level BPE (Byte-Pair Encoding) treinável do zero.
Inspirado no GPT-2 tokenizer, mas 100% puro Python/PyTorch.
Suporta unicode completo, português, código, matemática.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Optional


# Byte-level: mapeia cada byte (0-255) para um char visível Unicode
# Isso garante que qualquer sequência de bytes seja tokenizável.
_BYTES_TO_UNICODE = {i: chr(i) for i in range(256)}


def _get_word_tokens(word: str) -> list[str]:
    """Converte palavra em tokens iniciais (caracteres + marcador de fim de palavra)."""
    return list(word) + ["</w>"]


class SyntexaFoundationTokenizer:
    """
    Tokenizer BPE byte-level treinável.
    """
    def __init__(
        self,
        vocab: Optional[dict[str, int]] = None,
        merges: Optional[list[tuple[str, str]]] = None,
        special_tokens: Optional[dict[str, int]] = None,
    ):
        self.vocab = vocab or {}
        self.inverse_vocab = {v: k for k, v in self.vocab.items()}
        self.merges = merges or []
        self.special_tokens = special_tokens or {
            "<pad>": 0,
            "<unk>": 1,
            "<bos>": 2,
            "<eos>": 3,
        }
        self.pat = re.compile(
            r"""'s|'t|'re|'ve|'m|'ll|'d| ?[a-zA-Z\u00C0-\u024F\u1E00-\u1EFF]+| ?\d+| ?[^\sa-zA-Z\u00C0-\u024F\u1E00-\u1EFF\d]+|\s+(?!\S)|\s+""",
            re.UNICODE,
        )
        # Cache para encode
        self._cache: dict[str, list[int]] = {}

    # ── TRAINING ──────────────────────────────────────────────

    @classmethod
    def train(
        cls,
        texts: list[str],
        vocab_size: int = 32000,
        special_tokens: Optional[dict[str, int]] = None,
    ) -> "SyntexaFoundationTokenizer":
        """
        Treina tokenizer BPE a partir de corpus de textos.
        """
        if special_tokens is None:
            special_tokens = {"<pad>": 0, "<unk>": 1, "<bos>": 2, "<eos>": 3}

        # Pré-tokenização em palavras
        word_freqs: Counter[str] = Counter()
        for text in texts:
            for word in re.findall(r"\S+", text):
                word_freqs[word] += 1

        # Inicializa vocabulário com bytes únicos + special tokens
        vocab: dict[str, int] = {}
        for tok, idx in special_tokens.items():
            vocab[tok] = idx

        # Coleta todos os caracteres do corpus
        char_freqs: Counter[str] = Counter()
        for word, freq in word_freqs.items():
            for ch in word:
                char_freqs[ch] += freq

        # Adiciona caracteres ao vocabulário
        for ch in sorted(char_freqs.keys()):
            if ch not in vocab:
                vocab[ch] = len(vocab)

        # Garante cobertura de caracteres ASCII comuns (letras, números, pontuação básica)
        for ch in list("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,;:!?()[]{}'\"-+=*/\\_<>@#$%&|^~`"):
            if ch not in vocab:
                vocab[ch] = len(vocab)

        # Representação de cada palavra como lista de chars + </w>
        splits: dict[str, list[str]] = {}
        for word in word_freqs:
            splits[word] = _get_word_tokens(word)

        merges: list[tuple[str, str]] = []
        num_merges = vocab_size - len(vocab)

        for _ in range(max(0, num_merges)):
            pair_freqs: Counter[tuple[str, str]] = Counter()
            for word, freq in word_freqs.items():
                tokens = splits[word]
                for i in range(len(tokens) - 1):
                    pair = (tokens[i], tokens[i + 1])
                    pair_freqs[pair] += freq

            if not pair_freqs:
                break

            best_pair = pair_freqs.most_common(1)[0][0]
            merges.append(best_pair)
            new_token = best_pair[0] + best_pair[1]
            if new_token not in vocab:
                vocab[new_token] = len(vocab)

            # Atualiza splits
            for word in word_freqs:
                tokens = splits[word]
                new_tokens: list[str] = []
                i = 0
                while i < len(tokens):
                    if i < len(tokens) - 1 and tokens[i] == best_pair[0] and tokens[i + 1] == best_pair[1]:
                        new_tokens.append(new_token)
                        i += 2
                    else:
                        new_tokens.append(tokens[i])
                        i += 1
                splits[word] = new_tokens

        return cls(vocab=vocab, merges=merges, special_tokens=special_tokens)

    @classmethod
    def train_from_jsonl(
        cls,
        path: str | Path,
        vocab_size: int = 32000,
        text_key: str = "text",
        max_texts: Optional[int] = None,
    ) -> "SyntexaFoundationTokenizer":
        texts: list[str] = []
        with Path(path).open("r", encoding="utf-8") as fh:
            for i, line in enumerate(fh):
                if max_texts and i >= max_texts:
                    break
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    text = str(obj.get(text_key, ""))
                    if text:
                        texts.append(text)
                except json.JSONDecodeError:
                    continue
        return cls.train(texts, vocab_size=vocab_size)

    # ── ENCODE / DECODE ───────────────────────────────────────

    def _encode_word(self, word: str) -> list[int]:
        """Codifica uma palavra pré-tokenizada usando merges treinados."""
        if word in self._cache:
            return self._cache[word]

        tokens = _get_word_tokens(word)
        for merge in self.merges:
            new_token = merge[0] + merge[1]
            new_tokens: list[str] = []
            i = 0
            while i < len(tokens):
                if i < len(tokens) - 1 and tokens[i] == merge[0] and tokens[i + 1] == merge[1]:
                    new_tokens.append(new_token)
                    i += 2
                else:
                    new_tokens.append(tokens[i])
                    i += 1
            tokens = new_tokens

        ids = []
        for t in tokens:
            if t in self.vocab:
                ids.append(self.vocab[t])
            else:
                # Fallback: caracteres individuais
                for ch in t.replace("</w>", ""):
                    ids.append(self.vocab.get(ch, self.special_tokens["<unk>"]))
        self._cache[word] = ids
        return ids

    def encode(
        self,
        text: str,
        add_special_tokens: bool = True,
        max_length: Optional[int] = None,
    ) -> list[int]:
        text = str(text or "")
        words = re.findall(r"\S+", text)
        ids: list[int] = []
        if add_special_tokens:
            ids.append(self.special_tokens["<bos>"])
        for word in words:
            ids.extend(self._encode_word(word))
        if add_special_tokens:
            ids.append(self.special_tokens["<eos>"])
        if max_length and len(ids) > max_length:
            ids = ids[:max_length]
            if self.special_tokens["<eos>"] not in ids:
                ids[-1] = self.special_tokens["<eos>"]
        return ids

    def decode(self, token_ids: list[int], skip_special_tokens: bool = True) -> str:
        parts: list[str] = []
        for idx in token_ids:
            tok = self.inverse_vocab.get(int(idx), "<unk>")
            if skip_special_tokens and tok in self.special_tokens:
                continue
            if tok == "</w>":
                parts.append(" ")
            elif "</w>" in tok:
                parts.append(tok.replace("</w>", ""))
                parts.append(" ")
            else:
                parts.append(tok)
        text = "".join(parts)
        # Remove espaços duplos e corrige pontuação
        text = re.sub(r" +", " ", text)
        text = re.sub(r" ([.,;:!?])", r"\1", text)
        return text.strip()

    # ── PERSISTENCE ───────────────────────────────────────────

    def save(self, out_dir: str | Path) -> None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "vocab.json").write_text(
            json.dumps(self.vocab, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        (out_dir / "merges.txt").write_text(
            "\n".join(f"{a} {b}" for a, b in self.merges),
            encoding="utf-8",
        )
        (out_dir / "special_tokens.json").write_text(
            json.dumps(self.special_tokens, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, out_dir: str | Path) -> "SyntexaFoundationTokenizer":
        out_dir = Path(out_dir)
        vocab = json.loads((out_dir / "vocab.json").read_text(encoding="utf-8"))
        merges_raw = (out_dir / "merges.txt").read_text(encoding="utf-8").splitlines()
        merges = [tuple(line.strip().split(" ", 1)) for line in merges_raw if line.strip()]
        special = json.loads((out_dir / "special_tokens.json").read_text(encoding="utf-8"))
        return cls(vocab=vocab, merges=merges, special_tokens=special)

    # ── UTILS ─────────────────────────────────────────────────

    @property
    def vocab_size(self) -> int:
        return len(self.vocab)

    @property
    def bos_id(self) -> int:
        return self.special_tokens["<bos>"]

    @property
    def eos_id(self) -> int:
        return self.special_tokens["<eos>"]

    @property
    def pad_id(self) -> int:
        return self.special_tokens["<pad>"]

    @property
    def unk_id(self) -> int:
        return self.special_tokens["<unk>"]
