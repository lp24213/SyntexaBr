# -*- coding: utf-8 -*-
"""
Context compression for low-memory LLM inference. Reduces token usage before sending to model.
"""
import re
from typing import Any, Callable, List, Optional


def truncate_by_tokens(
    text: str,
    max_tokens: int = 1024,
    token_estimator: Optional[Callable[[str], Any]] = None,
) -> str:
    """Truncate text to approximately max_tokens. Default: ~4 chars per token."""
    if token_estimator:
        # If backend provides a tokenizer, use it for exact count
        tokens = token_estimator(text)
        if len(tokens) <= max_tokens:
            return text
        if hasattr(token_estimator, "decode"):
            return token_estimator.decode(tokens[:max_tokens])
        return text[: max_tokens * 4]
    approx_chars = max_tokens * 4
    if len(text) <= approx_chars:
        return text
    return text[:approx_chars].rsplit(" ", 1)[0] + "…"


def compress_context(
    snippets: List[str],
    max_total_tokens: int = 2048,
    separator: str = "\n\n",
    token_estimator: Optional[callable] = None,
) -> str:
    """
    Concatenate snippets and truncate to max_total_tokens. Preserves order; fills from start.
    """
    combined = separator.join(s for s in snippets if (s and s.strip()))
    return truncate_by_tokens(combined, max_tokens=max_total_tokens, token_estimator=token_estimator)


def compress_context_sentences(
    text: str,
    max_sentences: int = 30,
) -> str:
    """Keep first max_sentences sentences. Lightweight for summarization."""
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return " ".join(sentences[:max_sentences]).strip()
