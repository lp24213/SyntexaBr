from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


class SyntexaTokenizer:
    def __init__(self, token_to_id: dict[str, int]):
        self.token_to_id = token_to_id
        self.id_to_token = {v: k for k, v in token_to_id.items()}
        self.unk_id = token_to_id.get("<unk>", 1)
        self.bos_id = token_to_id.get("<bos>", 2)
        self.eos_id = token_to_id.get("<eos>", 3)

    @classmethod
    def train_from_jsonl(
        cls,
        jsonl_path: str | Path,
        *,
        vocab_size: int = 32000,
        text_key: str = "text",
    ) -> "SyntexaTokenizer":
        counter: Counter[str] = Counter()
        p = Path(jsonl_path)
        with p.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                text = str(obj.get(text_key, ""))
                toks = re.findall(r"\w+|[^\w\s]", text.lower(), flags=re.UNICODE)
                counter.update(toks)
        base = ["<pad>", "<unk>", "<bos>", "<eos>"]
        most_common = [t for t, _ in counter.most_common(max(0, vocab_size - len(base)))]
        tok_to_id = {t: i for i, t in enumerate(base + most_common)}
        return cls(tok_to_id)

    def encode(self, text: str, *, add_special_tokens: bool = True, max_length: int | None = None) -> list[int]:
        toks = re.findall(r"\w+|[^\w\s]", str(text or "").lower(), flags=re.UNICODE)
        ids = [self.token_to_id.get(t, self.unk_id) for t in toks]
        if add_special_tokens:
            ids = [self.bos_id] + ids + [self.eos_id]
        if max_length and max_length > 0:
            ids = ids[:max_length]
        return ids

    def decode(self, token_ids: list[int]) -> str:
        parts: list[str] = []
        for i in token_ids:
            if i in (self.bos_id, self.eos_id):
                continue
            parts.append(self.id_to_token.get(int(i), "<unk>"))
        return " ".join(parts).replace(" ,", ",").replace(" .", ".")

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.token_to_id, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "SyntexaTokenizer":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls({str(k): int(v) for k, v in data.items()})
