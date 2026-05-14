"""
VEREDA / SYNTEXA — Context Manager
=====================================
Gerenciamento inteligente de contexto com:
- Sliding window
- Semantic relevance scoring
- Compression de contexto
- Priority-based eviction
"""

import time
import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

log = logging.getLogger(__name__)


class MessageRole(Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    REASONING = "reasoning"


@dataclass
class ContextMessage:
    role: MessageRole
    content: str
    timestamp: float = field(default_factory=time.time)
    tokens: int = 0
    importance: float = 1.0  # 0-1, para eviction prioritária
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContextManager:
    """
    Gerenciador de contexto de conversação.
    Mantém janela deslizante com preservação de mensagens importantes.
    """

    def __init__(
        self,
        max_tokens: int = 8192,
        max_messages: int = 48,
        reserve_tokens: int = 512,  # reserva para resposta
    ):
        self.max_tokens = max_tokens
        self.max_messages = max_messages
        self.reserve_tokens = reserve_tokens
        self.messages: List[ContextMessage] = []
        self._token_count = 0
        self._session_id: Optional[str] = None

    # ── MESSAGE OPERATIONS ───────────────────────────────────
    def add_message(
        self,
        role: MessageRole,
        content: str,
        importance: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
        token_count: Optional[int] = None,
    ) -> None:
        msg = ContextMessage(
            role=role,
            content=content,
            importance=importance,
            metadata=metadata or {},
            tokens=token_count or self._estimate_tokens(content),
        )
        self.messages.append(msg)
        self._token_count += msg.tokens
        self._enforce_limits()

    def add_system_message(self, content: str) -> None:
        self.add_message(MessageRole.SYSTEM, content, importance=2.0)

    def add_user_message(self, content: str, importance: float = 1.0) -> None:
        self.add_message(MessageRole.USER, content, importance)

    def add_assistant_message(self, content: str, importance: float = 1.0) -> None:
        self.add_message(MessageRole.ASSISTANT, content, importance)

    def add_reasoning(self, content: str) -> None:
        self.add_message(MessageRole.REASONING, content, importance=1.5)

    # ── CONTEXT ENFORCEMENT ──────────────────────────────────
    def _enforce_limits(self) -> None:
        """Garante que contexto não excede limites."""
        # Limite de mensagens
        while len(self.messages) > self.max_messages:
            removed = self.messages.pop(0)
            self._token_count -= removed.tokens

        # Limite de tokens (com eviction inteligente)
        available = self.max_tokens - self.reserve_tokens
        while self._token_count > available and len(self.messages) > 1:
            # Encontra mensagem menos importante (que não seja system)
            evict_idx = self._find_evict_candidate()
            if evict_idx is None:
                break
            removed = self.messages.pop(evict_idx)
            self._token_count -= removed.tokens
            log.debug("Evicted message: role=%s, tokens=%d", removed.role.value, removed.tokens)

    def _find_evict_candidate(self) -> Optional[int]:
        """Encontra índice da mensagem mais indicada para eviction."""
        candidates = []
        for i, msg in enumerate(self.messages):
            if msg.role == MessageRole.SYSTEM:
                continue  # Nunca evict system
            score = msg.importance - (time.time() - msg.timestamp) / 3600  # penaliza antigas
            candidates.append((score, i))

        if not candidates:
            return None
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]

    # ── CONTEXT BUILDING ─────────────────────────────────────
    def build_context(self, include_reasoning: bool = False) -> List[Dict[str, str]]:
        """Constrói lista de mensagens para o modelo."""
        result = []
        for msg in self.messages:
            if msg.role == MessageRole.REASONING and not include_reasoning:
                continue
            result.append({
                "role": msg.role.value,
                "content": msg.content,
            })
        return result

    def build_prompt(self, tokenizer=None) -> str:
        """Constrói prompt string a partir do contexto."""
        parts = []
        for msg in self.messages:
            if msg.role == MessageRole.SYSTEM:
                parts.append(f"System: {msg.content}")
            elif msg.role == MessageRole.USER:
                parts.append(f"User: {msg.content}")
            elif msg.role == MessageRole.ASSISTANT:
                parts.append(f"Assistant: {msg.content}")
            elif msg.role == MessageRole.REASONING:
                parts.append(f"[Reasoning: {msg.content}]")
        return "\n\n".join(parts) + "\n\nAssistant:"

    # ── SEMANTIC RELEVANCE ───────────────────────────────────
    def score_relevance(self, query: str, tokenizer=None) -> List[Tuple[int, float]]:
        """
        Score de relevância semântica de cada mensagem em relação à query.
        Simplificado: keyword overlap.
        """
        query_words = set(query.lower().split())
        scores = []
        for i, msg in enumerate(self.messages):
            msg_words = set(msg.content.lower().split())
            overlap = len(query_words & msg_words)
            scores.append((i, overlap / max(len(query_words), 1)))
        return sorted(scores, key=lambda x: x[1], reverse=True)

    def compress_context(self, tokenizer=None, keep_ratio: float = 0.7) -> None:
        """
        Comprime contexto mantendo apenas mensagens mais relevantes.
        """
        if len(self.messages) <= 3:
            return

        # Calcular importância acumulada
        for msg in self.messages:
            msg.importance = min(2.0, msg.importance + 0.1)  # bonus por permanência

        # Target de tokens
        target_tokens = int(self.max_tokens * keep_ratio)
        available = target_tokens - self.reserve_tokens

        while self._token_count > available and len(self.messages) > 2:
            evict_idx = self._find_evict_candidate()
            if evict_idx is None:
                break
            removed = self.messages.pop(evict_idx)
            self._token_count -= removed.tokens

        log.info("Context compressed: %d messages, %d tokens", len(self.messages), self._token_count)

    # ── SUMMARIZATION ────────────────────────────────────────
    def get_summary(self, max_chars: int = 500) -> str:
        """Gera resumo do contexto atual."""
        recent = self.messages[-5:] if len(self.messages) > 5 else self.messages
        summary_parts = []
        for msg in recent:
            prefix = {
                MessageRole.USER: "Q:",
                MessageRole.ASSISTANT: "A:",
                MessageRole.SYSTEM: "S:",
                MessageRole.REASONING: "R:",
            }.get(msg.role, "M:")
            content = msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
            summary_parts.append(f"{prefix} {content}")
        summary = " | ".join(summary_parts)
        return summary[:max_chars]

    # ── SESSION MANAGEMENT ───────────────────────────────────
    def set_session(self, session_id: str) -> None:
        self._session_id = session_id

    def get_session(self) -> Optional[str]:
        return self._session_id

    def clear(self) -> None:
        self.messages.clear()
        self._token_count = 0
        log.info("Context cleared")

    # ── STATS ────────────────────────────────────────────────
    def get_stats(self) -> Dict[str, Any]:
        return {
            "messages": len(self.messages),
            "tokens": self._token_count,
            "max_tokens": self.max_tokens,
            "utilization": round(self._token_count / self.max_tokens, 3),
            "session_id": self._session_id,
        }

    def _estimate_tokens(self, text: str) -> int:
        # Estimativa simples: ~4 chars por token
        return max(1, len(text) // 4)
