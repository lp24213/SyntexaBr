# -*- coding: utf-8 -*-
"""
Memória de conversa para o pipeline de resposta — delega ao MemorySystem já existente.
"""
from __future__ import annotations

from typing import Any, List


def retrieve_conversation_memory(query: str, top_k: int = 3) -> List[dict]:
    from vereda_backend.ai_runtime import memory_system

    return memory_system.retrieve_context(query, top_k=top_k)


def add_turn(conv_id: str, role: str, content: str) -> None:
    from vereda_backend.ai_runtime import conversation_memory

    conversation_memory.add_turn(conv_id, role, content)
