"""
SYNTEXA DATASET PIPELINE
========================
Pipeline de dados soberano para treinamento da Foundation Model.
Carrega, limpa, deduplica, filtra e balanceia dados de múltiplas fontes.
Fontes: Common Crawl, Wikipedia, livros, código, StackExchange, PDFs, OCR, etc.
"""
from __future__ import annotations

import hashlib
import json
import logging
import random
import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

import numpy as np

log = logging.getLogger(__name__)


class TextCleaner:
    """Limpa e normaliza textos para treinamento."""

    @staticmethod
    def clean(text: str) -> str:
        if not text:
            return ""
        # Remove controle de caracteres
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
        # Normaliza whitespace
        text = re.sub(r"\s+", " ", text)
        # Remove URLs (opcional, manter se quiser treinar com URLs)
        # text = re.sub(r"https?://\S+", "", text)
        # Remove emails
        text = re.sub(r"\S+@\S+\.\S+", "", text)
        # Normaliza aspas
        text = text.replace("''", '"').replace("``", '"')
        # Remove linhas com apenas símbolos
        lines = text.split("\n")
        cleaned_lines = []
        for line in lines:
            if len(line.strip()) > 0 and not re.match(r"^[\W_]+$", line.strip()):
                cleaned_lines.append(line.strip())
        return "\n".join(cleaned_lines).strip()

    @staticmethod
    def dedup_lines(texts: List[str], threshold: float = 0.85) -> List[str]:
        """Deduplica textos por similaridade de n-grams."""
        seen_hashes: set[str] = set()
        out: list[str] = []
        for t in texts:
            h = hashlib.sha256(t.encode("utf-8")).hexdigest()[:32]
            if h in seen_hashes:
                continue
            seen_hashes.add(h)
            out.append(t)
        log.info("[DatasetPipeline] Deduplicação: %d -> %d textos", len(texts), len(out))
        return out


class QualityScorer:
    """Pontua qualidade de textos para curriculum learning."""

    def __init__(self):
        self.min_length = 50
        self.max_length = 100000

    def score(self, text: str) -> float:
        if not text:
            return 0.0
        length = len(text)
        if length < self.min_length or length > self.max_length:
            return 0.0

        scores = []

        # 1. Razão palavras/total_tokens (evita lixo binário)
        words = len(re.findall(r"\w+", text))
        scores.append(min(1.0, words / max(length * 0.1, 1)))

        # 2. Diversidade lexical
        unique_words = len(set(w.lower() for w in re.findall(r"\w+", text)))
        scores.append(min(1.0, unique_words / max(words * 0.5, 1)))

        # 3. Proporção de pontuação razoável
        punct_ratio = len(re.findall(r"[.,;:!?]", text)) / max(length, 1)
        scores.append(1.0 if 0.01 < punct_ratio < 0.3 else 0.5)

        # 4. Presença de código (bonus para código bem formatado)
        code_blocks = len(re.findall(r"```[\s\S]*?```", text))
        if code_blocks > 0:
            scores.append(0.9)

        # 5. Presença de markdown estruturado
        md_headers = len(re.findall(r"^#{1,6}\s", text, re.M))
        if md_headers > 0:
            scores.append(0.85)

        return float(np.mean(scores))


class DatasetCurator:
    """
    Curador de dataset que coleta de múltiplas fontes,
    limpa, deduplica, pontua e balanceia.
    """

    def __init__(self, output_path: str = "data/curated.jsonl"):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.cleaner = TextCleaner()
        self.scorer = QualityScorer()
        self.samples: list[dict[str, Any]] = []

    def load_jsonl(self, path: str | Path, text_key: str = "text") -> None:
        p = Path(path)
        if not p.is_file():
            log.warning("[DatasetPipeline] Arquivo não encontrado: %s", p)
            return
        count = 0
        with p.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    text = str(obj.get(text_key, "")).strip()
                    if len(text) >= 50:
                        self.samples.append({"text": text, "source": str(p.name), "meta": obj.get("meta", {})})
                        count += 1
                except json.JSONDecodeError:
                    continue
        log.info("[DatasetPipeline] Carregados %d amostras de %s", count, p)

    def load_txt(self, path: str | Path) -> None:
        p = Path(path)
        if not p.is_file():
            return
        text = p.read_text(encoding="utf-8", errors="ignore")
        chunks = self._chunk_text(text, max_chars=2000)
        for chunk in chunks:
            if len(chunk) >= 50:
                self.samples.append({"text": chunk, "source": str(p.name), "meta": {}})
        log.info("[DatasetPipeline] Carregados %d chunks de %s", len(chunks), p)

    def load_directory(self, dir_path: str | Path, pattern: str = "*.jsonl") -> None:
        d = Path(dir_path)
        if not d.is_dir():
            return
        for f in d.glob(pattern):
            if f.suffix == ".jsonl":
                self.load_jsonl(f)
            elif f.suffix in (".txt", ".md"):
                self.load_txt(f)

    def _chunk_text(self, text: str, max_chars: int = 2000, overlap: int = 200) -> list[str]:
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + max_chars, len(text))
            # Tenta quebrar em fim de frase
            if end < len(text):
                for sep in (".\n", "\n\n", ". ", " "):
                    pos = text.rfind(sep, start, end)
                    if pos != -1:
                        end = pos + len(sep)
                        break
            chunk = text[start:end].strip()
            if len(chunk) >= 50:
                chunks.append(chunk)
            start = end - overlap
        return chunks

    def clean(self) -> None:
        """Limpa todos os textos."""
        for s in self.samples:
            s["text"] = self.cleaner.clean(s["text"])
        self.samples = [s for s in self.samples if len(s["text"]) >= 50]
        log.info("[DatasetPipeline] Após limpeza: %d amostras", len(self.samples))

    def deduplicate(self) -> None:
        """Deduplica textos."""
        texts = [s["text"] for s in self.samples]
        unique_texts = self.cleaner.dedup_lines(texts)
        # Reconstrói samples preservando metadados do primeiro
        seen = set()
        new_samples = []
        for s in self.samples:
            if s["text"] in unique_texts and s["text"] not in seen:
                seen.add(s["text"])
                new_samples.append(s)
        self.samples = new_samples
        log.info("[DatasetPipeline] Após deduplicação: %d amostras", len(self.samples))

    def score(self) -> None:
        """Pontua qualidade de cada amostra."""
        for s in self.samples:
            s["quality_score"] = self.scorer.score(s["text"])
        log.info("[DatasetPipeline] Qualidade média: %.3f", np.mean([s["quality_score"] for s in self.samples]))

    def filter_by_quality(self, min_score: float = 0.3) -> None:
        """Filtra amostras por score mínimo."""
        before = len(self.samples)
        self.samples = [s for s in self.samples if s.get("quality_score", 0) >= min_score]
        log.info("[DatasetPipeline] Filtragem: %d -> %d amostras (min_score=%.2f)", before, len(self.samples), min_score)

    def balance_languages(self, target_ratio: Optional[Dict[str, float]] = None) -> None:
        """
        Balanceia dataset por idioma detectado.
        target_ratio: ex: {'pt': 0.4, 'en': 0.4, 'es': 0.1, 'code': 0.1}
        """
        if target_ratio is None:
            target_ratio = {"pt": 0.35, "en": 0.35, "es": 0.1, "code": 0.15, "other": 0.05}

        def detect_lang(text: str) -> str:
            # Heurística simples
            code_keywords = ["def ", "class ", "import ", "function", "const ", "let ", "var ", "#include"]
            if any(kw in text for kw in code_keywords):
                return "code"
            pt_words = ["de", "do", "da", "para", "como", "que", "não", "sim", "mais", "muito"]
            en_words = ["the", "and", "for", "with", "from", "this", "that", "have", "been", "were"]
            es_words = ["el", "la", "de", "que", "en", "un", "ser", "se", "por", "con"]
            text_lower = text.lower()
            pt_count = sum(1 for w in pt_words if w in text_lower)
            en_count = sum(1 for w in en_words if w in text_lower)
            es_count = sum(1 for w in es_words if w in text_lower)
            counts = {"pt": pt_count, "en": en_count, "es": es_count}
            best = max(counts, key=counts.get)
            if counts[best] > 2:
                return best
            return "other"

        # Agrupa por idioma
        by_lang: dict[str, list] = {}
        for s in self.samples:
            lang = detect_lang(s["text"])
            s["lang"] = lang
            by_lang.setdefault(lang, []).append(s)

        total_target = len(self.samples)
        balanced = []
        for lang, ratio in target_ratio.items():
            available = by_lang.get(lang, [])
            target_count = int(total_target * ratio)
            if len(available) > target_count:
                balanced.extend(random.sample(available, target_count))
            else:
                balanced.extend(available)

        self.samples = balanced
        log.info("[DatasetPipeline] Balanceamento: %d amostras", len(self.samples))
        for lang, samples in by_lang.items():
            count = sum(1 for s in self.samples if s.get("lang") == lang)
            log.info("  %s: %d amostras", lang, count)

    def export(self) -> Path:
        """Exporta dataset curado para JSONL."""
        with self.output_path.open("w", encoding="utf-8") as fh:
            for s in self.samples:
                fh.write(json.dumps(s, ensure_ascii=False) + "\n")
        log.info("[DatasetPipeline] Exportado: %s (%d amostras)", self.output_path, len(self.samples))
        return self.output_path

    def run_full_pipeline(
        self,
        sources: list[str],
        min_quality: float = 0.3,
        balance: bool = True,
    ) -> Path:
        """Executa pipeline completo: load -> clean -> dedup -> score -> filter -> balance -> export."""
        for src in sources:
            p = Path(src)
            if p.is_dir():
                self.load_directory(src)
            elif p.is_file():
                if p.suffix == ".jsonl":
                    self.load_jsonl(src)
                elif p.suffix in (".txt", ".md"):
                    self.load_txt(src)
        log.info("[DatasetPipeline] Total carregado: %d amostras", len(self.samples))
        self.clean()
        self.deduplicate()
        self.score()
        self.filter_by_quality(min_quality)
        if balance:
            self.balance_languages()
        return self.export()
