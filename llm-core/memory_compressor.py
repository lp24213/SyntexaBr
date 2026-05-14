"""
VEREDA / SYNTEXA — Memory Compressor
======================================
Compressão de memória de contexto com:
- Semantic summarization
- Lossy compression
- Hierarchical memory
- Embedding-based retrieval
"""

import re
import time
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

try:
    import numpy as np
except ImportError:
    np = None

log = logging.getLogger(__name__)


@dataclass
class CompressedMemory:
    summary: str
    details: List[str]
    timestamp: float = field(default_factory=time.time)
    importance: float = 1.0
    embeddings: Optional[List[float]] = None


class MemoryCompressor:
    """
    Comprime memória de conversação mantendo semântica.
    Usa hierarquia: short-term → compressed → long-term.
    """

    def __init__(
        self,
        max_short_term_items: int = 20,
        max_compressed_items: int = 100,
        compression_ratio: float = 0.3,
    ):
        self.max_short_term = max_short_term_items
        self.max_compressed = max_compressed_items
        self.compression_ratio = compression_ratio

        self._short_term: List[Dict[str, Any]] = []
        self._compressed: List[CompressedMemory] = []
        self._long_term: List[CompressedMemory] = []

    # ── SHORT-TERM MEMORY ────────────────────────────────────
    def add(self, role: str, content: str, importance: float = 1.0) -> None:
        """Adiciona item à memória de curto prazo."""
        self._short_term.append({
            "role": role,
            "content": content,
            "timestamp": time.time(),
            "importance": importance,
        })
        if len(self._short_term) > self.max_short_term:
            self._compress_oldest()

    # ── COMPRESSION ──────────────────────────────────────────
    def _compress_oldest(self) -> None:
        """Comprime os itens mais antigos para memória comprimida."""
        n_compress = max(1, int(len(self._short_term) * 0.3))
        to_compress = self._short_term[:n_compress]
        self._short_term = self._short_term[n_compress:]

        # Gerar sumário
        summary = self._summarize_batch(to_compress)
        details = [item["content"][:200] for item in to_compress]

        compressed = CompressedMemory(
            summary=summary,
            details=details,
            importance=max(item.get("importance", 1.0) for item in to_compress),
        )
        self._compressed.append(compressed)

        if len(self._compressed) > self.max_compressed:
            self._archive_oldest()

    def _summarize_batch(self, items: List[Dict[str, Any]]) -> str:
        """Gera sumário de um batch de mensagens."""
        # Extrai tópicos principais
        all_text = " ".join(item["content"] for item in items)
        sentences = re.split(r'[.!?]+', all_text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 10]

        # Seleciona sentenças representativas
        if len(sentences) <= 3:
            return all_text[:500]

        # Heurística: sentenças com mais keywords
        keywords = self._extract_keywords(all_text)
        scored = []
        for sent in sentences:
            score = sum(1 for kw in keywords if kw.lower() in sent.lower())
            scored.append((score, sent))

        scored.sort(reverse=True)
        top_sentences = [s for _, s in scored[:3]]
        return " ".join(top_sentences)

    def _extract_keywords(self, text: str) -> List[str]:
        """Extrai keywords por frequência."""
        words = re.findall(r'\b\w{4,}\b', text.lower())
        from collections import Counter
        counts = Counter(words)
        # Remove stopwords simples
        stopwords = {"esta", "esse", "aquele", "para", "como", "quando", "onde", "porque", "this", "that", "with", "from", "have", "been"}
        filtered = {w: c for w, c in counts.items() if w not in stopwords}
        return [w for w, _ in sorted(filtered.items(), key=lambda x: x[1], reverse=True)[:10]]

    # ── ARCHIVE ──────────────────────────────────────────────
    def _archive_oldest(self) -> None:
        """Move memória comprimida antiga para long-term."""
        n_archive = max(1, len(self._compressed) // 4)
        to_archive = self._compressed[:n_archive]
        self._compressed = self._compressed[n_archive:]
        self._long_term.extend(to_archive)
        log.debug("Archived %d compressed memories to long-term", n_archive)

    # ── RETRIEVAL ────────────────────────────────────────────
    def retrieve_relevant(self, query: str, top_k: int = 5) -> List[str]:
        """Recupera memórias relevantes para a query."""
        query_keywords = set(self._extract_keywords(query))
        scored = []

        # Score de todas as memórias
        for mem in self._short_term + [m.__dict__ for m in self._compressed] + [m.__dict__ for m in self._long_term]:
            if isinstance(mem, dict):
                text = mem.get("content", "") or mem.get("summary", "")
            else:
                text = mem.summary

            mem_keywords = set(self._extract_keywords(text))
            overlap = len(query_keywords & mem_keywords)
            scored.append((overlap, text))

        scored.sort(reverse=True)
        return [text for _, text in scored[:top_k] if len(text) > 5]

    # ── FULL RECALL ──────────────────────────────────────────
    def get_all_memories(self) -> Dict[str, Any]:
        return {
            "short_term": len(self._short_term),
            "compressed": len(self._compressed),
            "long_term": len(self._long_term),
            "total_items": len(self._short_term) + len(self._compressed) + len(self._long_term),
        }

    def clear(self) -> None:
        self._short_term.clear()
        self._compressed.clear()
        self._long_term.clear()
