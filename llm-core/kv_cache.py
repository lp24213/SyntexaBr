"""
VEREDA / SYNTEXA — KV Cache Manager
=====================================
Gerenciamento inteligente de KV cache com:
- LRU eviction
- Memory compression (quantization)
- Multi-turn persistence
- Sliding window
"""

import math
import time
import logging
from typing import Dict, List, Optional, Tuple, Any
from collections import OrderedDict
from dataclasses import dataclass, field

try:
    import torch
except ImportError:
    torch = None

log = logging.getLogger(__name__)


@dataclass
class KVCacheEntry:
    key: Any   # torch.Tensor ou numpy array
    value: Any
    seq_len: int
    timestamp: float = field(default_factory=time.time)
    access_count: int = 0
    compressed: bool = False


class KVCacheManager:
    """
    Gerenciador de KV cache para inferência eficiente.
    Mantém cache por sessão com eviction LRU.
    """

    def __init__(
        self,
        max_entries: int = 1000,
        max_seq_len: int = 8192,
        compression_ratio: float = 0.5,
        device: str = "cuda",
    ):
        self.max_entries = max_entries
        self.max_seq_len = max_seq_len
        self.compression_ratio = compression_ratio
        self.device = device

        # Cache por session_id
        self._cache: OrderedDict[str, KVCacheEntry] = OrderedDict()
        self._total_memory_mb = 0.0
        self._hits = 0
        self._misses = 0

    # ── CORE OPERATIONS ────────────────────────────────────
    def get(self, session_id: str) -> Optional[Tuple[Any, Any]]:
        """Recupera KV cache de uma sessão."""
        if session_id not in self._cache:
            self._misses += 1
            return None

        entry = self._cache[session_id]
        entry.access_count += 1
        entry.timestamp = time.time()
        self._cache.move_to_end(session_id)
        self._hits += 1

        # Decompress se necessário
        if entry.compressed and torch is not None:
            k = self._decompress(entry.key)
            v = self._decompress(entry.value)
            return (k, v)

        return (entry.key, entry.value)

    def set(self, session_id: str, key: Any, value: Any, seq_len: int) -> None:
        """Armazena KV cache de uma sessão."""
        # Evict se necessário
        while len(self._cache) >= self.max_entries:
            self._evict_lru()

        # Compress se seq_len grande
        compressed = False
        if seq_len > self.max_seq_len * 0.8 and torch is not None:
            key = self._compress(key)
            value = self._compress(value)
            compressed = True

        entry = KVCacheEntry(
            key=key,
            value=value,
            seq_len=seq_len,
            compressed=compressed,
        )
        self._cache[session_id] = entry
        self._update_memory_stats()

    def update(self, session_id: str, key: Any, value: Any, seq_len: int) -> None:
        """Atualiza cache existente (append tokens)."""
        existing = self._cache.get(session_id)
        if existing is not None and torch is not None and not existing.compressed:
            # Concatenar com cache anterior
            key = torch.cat([existing.key, key], dim=2)
            value = torch.cat([existing.value, value], dim=2)

        self.set(session_id, key, value, seq_len)

    def invalidate(self, session_id: str) -> None:
        """Remove cache de uma sessão."""
        if session_id in self._cache:
            del self._cache[session_id]
            self._update_memory_stats()

    def clear(self) -> None:
        """Limpa todo o cache."""
        self._cache.clear()
        self._total_memory_mb = 0.0
        log.info("KV cache cleared")

    # ── COMPRESSION ──────────────────────────────────────────
    def _compress(self, tensor: Any) -> Any:
        """Quantização 8-bit para reduzir memória."""
        if torch is None:
            return tensor
        # Simulação: em produção usar torch.quantization
        # ou bitsandbytes 8-bit
        return tensor.half() if tensor.dtype == torch.float32 else tensor

    def _decompress(self, tensor: Any) -> Any:
        if torch is None:
            return tensor
        return tensor.float() if tensor.dtype == torch.float16 else tensor

    # ── EVICTION ─────────────────────────────────────────────
    def _evict_lru(self) -> None:
        """Remove entrada menos recentemente usada."""
        oldest_key, oldest_entry = self._cache.popitem(last=False)
        log.debug("Evicted KV cache: session=%s (seq_len=%d)", oldest_key, oldest_entry.seq_len)
        self._update_memory_stats()

    def _evict_by_memory(self, target_mb: float) -> None:
        """Evict até liberar target_mb."""
        while self._total_memory_mb > target_mb and self._cache:
            self._evict_lru()

    # ── MEMORY STATS ─────────────────────────────────────────
    def _update_memory_stats(self) -> None:
        if torch is None:
            return
        total = 0.0
        for entry in self._cache.values():
            if hasattr(entry.key, "element_size"):
                total += (entry.key.numel() * entry.key.element_size()) / (1024 ** 2)
            if hasattr(entry.value, "element_size"):
                total += (entry.value.numel() * entry.value.element_size()) / (1024 ** 2)
        self._total_memory_mb = total

    # ── SLIDING WINDOW ───────────────────────────────────────
    def apply_sliding_window(
        self,
        session_id: str,
        window_size: int = 4096,
    ) -> Optional[Tuple[Any, Any]]:
        """
        Aplica janela deslizante no KV cache.
        Mantém apenas os últimos window_size tokens.
        """
        cached = self.get(session_id)
        if cached is None or torch is None:
            return cached

        k, v = cached
        seq_len = k.shape[2] if len(k.shape) >= 3 else k.shape[1]
        if seq_len <= window_size:
            return cached

        # Trunca para janela
        k = k[..., -window_size:, :]
        v = v[..., -window_size:, :]
        self.set(session_id, k, v, window_size)
        return (k, v)

    # ── MULTI-TURN PERSISTENCE ───────────────────────────────
    def get_conversation_key(self, conversation_id: str, turn: int) -> str:
        return f"conv:{conversation_id}:turn:{turn}"

    def persist_turn(
        self,
        conversation_id: str,
        turn: int,
        key: Any,
        value: Any,
        seq_len: int,
    ) -> None:
        """Persiste KV cache de um turno de conversação."""
        cache_key = self.get_conversation_key(conversation_id, turn)
        self.set(cache_key, key, value, seq_len)

    def load_conversation(
        self,
        conversation_id: str,
        max_turns: int = 10,
    ) -> Optional[Tuple[Any, Any]]:
        """Carrega cache acumulado de uma conversação."""
        if torch is None:
            return None

        all_k = []
        all_v = []
        total_len = 0

        for turn in range(max_turns):
            cache_key = self.get_conversation_key(conversation_id, turn)
            cached = self.get(cache_key)
            if cached is None:
                break
            k, v = cached
            all_k.append(k)
            all_v.append(v)
            total_len += k.shape[2] if len(k.shape) >= 3 else k.shape[1]

        if not all_k:
            return None

        # Concatenar todos os turnos
        k = torch.cat(all_k, dim=2 if len(all_k[0].shape) >= 3 else 1)
        v = torch.cat(all_v, dim=2 if len(all_v[0].shape) >= 3 else 1)
        return (k, v)

    # ── METRICS ──────────────────────────────────────────────
    def get_stats(self) -> Dict[str, Any]:
        total = len(self._cache)
        hit_rate = self._hits / max(self._hits + self._misses, 1)
        return {
            "entries": total,
            "memory_mb": round(self._total_memory_mb, 2),
            "max_entries": self.max_entries,
            "hit_rate": round(hit_rate, 3),
            "hits": self._hits,
            "misses": self._misses,
        }
