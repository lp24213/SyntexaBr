"""
VEREDA / SYNTEXA — Dynamic Batcher
=====================================
Batching inteligente com:
- Dynamic padding
- Bucketing por tamanho
- Continuous batching (in-flight)
- Request coalescing
"""

import time
import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from collections import deque

try:
    import torch
except ImportError:
    torch = None

log = logging.getLogger(__name__)


@dataclass
class BatchRequest:
    id: str
    prompt: str
    max_new_tokens: int = 128
    temperature: float = 0.7
    priority: int = 0  # menor = mais prioritário
    submit_time: float = field(default_factory=time.time)
    tokens_generated: int = 0
    is_complete: bool = False
    output_text: str = ""


class DynamicBatcher:
    """
    Batcher dinâmico que agrupa requests por tamanho similar.
    Suporta continuous batching (adiciona requests em batch em execução).
    """

    def __init__(
        self,
        max_batch_size: int = 8,
        max_wait_ms: float = 50.0,  # max tempo esperando para formar batch
        max_seq_len: int = 2048,
        padding_token_id: int = 0,
    ):
        self.max_batch_size = max_batch_size
        self.max_wait_ms = max_wait_ms
        self.max_seq_len = max_seq_len
        self.padding_token_id = padding_token_id

        self._pending: deque = deque()
        self._current_batch: List[BatchRequest] = []
        self._batch_start_time: Optional[float] = None

        # Buckets: divide requests em buckets de tamanho
        self._buckets: Dict[int, List[BatchRequest]] = {}
        self._bucket_size = 64  # tokens por bucket

    # ── REQUEST ENQUEUE ──────────────────────────────────────
    def enqueue(self, request: BatchRequest) -> None:
        """Adiciona request à fila."""
        self._pending.append(request)
        log.debug("Request %s enqueued", request.id)

    # ── BATCH FORMING ────────────────────────────────────────
    def try_form_batch(self, tokenizer=None) -> Optional[List[BatchRequest]]:
        """
        Tenta formar um batch ótimo da fila pendente.
        Usa bucketing para agrupar requests de tamanho similar.
        """
        if not self._pending:
            return None

        # Bucketização
        buckets: Dict[int, List[BatchRequest]] = {}
        now = time.time()

        for req in list(self._pending):
            # Estima tamanho do prompt (ou usa tokenizador real)
            est_tokens = len(req.prompt.split()) if tokenizer is None else len(tokenizer.encode(req.prompt))
            bucket_idx = est_tokens // self._bucket_size

            if bucket_idx not in buckets:
                buckets[bucket_idx] = []
            buckets[bucket_idx].append(req)

        # Escolhe bucket mais cheio que cabe no max_batch_size
        best_bucket = None
        best_count = 0
        for bucket_idx, reqs in buckets.items():
            count = len(reqs)
            # Prioriza requests que esperaram mais tempo
            urgent = sum(1 for r in reqs if (now - r.submit_time) * 1000 > self.max_wait_ms)
            score = count + urgent * 2
            if score > best_count and count <= self.max_batch_size:
                best_count = score
                best_bucket = bucket_idx

        if best_bucket is None:
            return None

        batch = buckets[best_bucket][:self.max_batch_size]

        # Remove da fila pendente
        batch_ids = {r.id for r in batch}
        self._pending = deque(r for r in self._pending if r.id not in batch_ids)

        self._current_batch = batch
        self._batch_start_time = time.time()
        return batch

    # ── CONTINUOUS BATCHING ──────────────────────────────────
    def add_to_running_batch(
        self,
        new_request: BatchRequest,
        current_batch: List[BatchRequest],
    ) -> Optional[List[BatchRequest]]:
        """
        Tenta adicionar novo request a batch em execução (continuous batching).
        Só funciona se houver VRAM disponível.
        """
        if len(current_batch) >= self.max_batch_size:
            return None

        # Verifica se há requests completados no batch
        completed = [r for r in current_batch if r.is_complete]
        if not completed:
            return None

        # Substitui request completado pelo novo
        for old_req in completed:
            current_batch.remove(old_req)
            current_batch.append(new_request)
            log.debug("Continuous batch: replaced %s with %s", old_req.id, new_request.id)
            return current_batch

        return None

    # ── BATCH PREPARATION ────────────────────────────────────
    def prepare_batch_inputs(
        self,
        batch: List[BatchRequest],
        tokenizer=None,
    ) -> Dict[str, Any]:
        """
        Prepara inputs para batch inference com dynamic padding.
        """
        if tokenizer is None or torch is None:
            return {}

        # Tokenize todos os prompts
        tokenized = []
        max_len = 0
        for req in batch:
            tokens = tokenizer.encode(req.prompt, add_special_tokens=True)
            tokenized.append(tokens)
            max_len = max(max_len, len(tokens))

        # Pad para max_len
        input_ids = []
        attention_masks = []
        for tokens in tokenized:
            padded = tokens + [self.padding_token_id] * (max_len - len(tokens))
            mask = [1] * len(tokens) + [0] * (max_len - len(tokens))
            input_ids.append(padded)
            attention_masks.append(mask)

        return {
            "input_ids": torch.tensor(input_ids, dtype=torch.long),
            "attention_mask": torch.tensor(attention_masks, dtype=torch.long),
            "max_new_tokens": max(r.max_new_tokens for r in batch),
            "temperature": sum(r.temperature for r in batch) / len(batch),
        }

    # ── BATCH DECODING ───────────────────────────────────────
    def decode_batch_outputs(
        self,
        batch: List[BatchRequest],
        output_ids: Any,
        tokenizer=None,
    ) -> None:
        """
        Decodifica outputs do batch e atualiza requests.
        """
        if tokenizer is None:
            return

        for i, req in enumerate(batch):
            if req.is_complete:
                continue

            # Extrai tokens gerados (após o prompt)
            # Simplificado: assume output_ids contém tokens gerados
            if hasattr(output_ids, '__len__') and i < len(output_ids):
                token_ids = output_ids[i] if len(output_ids.shape) > 1 else output_ids
                text = tokenizer.decode(token_ids, skip_special_tokens=True)
                req.output_text += text
                req.tokens_generated += len(token_ids) if hasattr(token_ids, '__len__') else 1

    # ── STATS ────────────────────────────────────────────────
    def get_stats(self) -> Dict[str, Any]:
        return {
            "pending": len(self._pending),
            "current_batch_size": len(self._current_batch),
            "max_batch_size": self.max_batch_size,
            "max_wait_ms": self.max_wait_ms,
        }
