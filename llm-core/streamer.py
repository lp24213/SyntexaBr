"""
VEREDA / SYNTEXA — Token Streamer
==================================
Engine de streaming token-por-token com:
- SSE formatting
- Adaptive buffering
- Latency optimization
- Backpressure handling
"""

import time
import asyncio
import logging
from typing import AsyncIterator, Iterator, Optional, Callable, Any, Dict
from dataclasses import dataclass, field

log = logging.getLogger(__name__)


@dataclass
class StreamConfig:
    chunk_size: int = 1          # tokens por chunk
    min_latency_ms: float = 10.0  # delay mínimo entre chunks
    max_latency_ms: float = 100.0  # delay máximo
    adaptive_buffer: bool = True
    enable_stats: bool = True


class TokenStreamer:
    """
    Streamer de tokens com formatação SSE e controle de latência.
    """

    def __init__(self, config: Optional[StreamConfig] = None):
        self.config = config or StreamConfig()
        self._buffer: list[str] = []
        self._total_tokens = 0
        self._start_time: Optional[float] = None
        self._last_emit_time: Optional[float] = None

    # ── SYNC STREAMING ───────────────────────────────────────
    def stream_tokens(
        self,
        token_generator: Iterator[str],
        formatter: Optional[Callable[[str], str]] = None,
    ) -> Iterator[str]:
        """
        Stream tokens síncrono com buffering adaptativo.
        """
        self._start_time = time.time()
        self._total_tokens = 0

        default_formatter = lambda t: f"data: {t}\n\n"
        fmt = formatter or default_formatter

        for token in token_generator:
            self._total_tokens += 1

            if self.config.adaptive_buffer:
                self._buffer.append(token)
                # Emit quando buffer atinge chunk_size ou token é pontuação
                if len(self._buffer) >= self.config.chunk_size or token in ".,!?;:\n":
                    chunk = "".join(self._buffer)
                    self._buffer.clear()
                    yield fmt(chunk)
                    self._throttle()
            else:
                yield fmt(token)
                self._throttle()

        # Flush buffer remaining
        if self._buffer:
            chunk = "".join(self._buffer)
            yield fmt(chunk)
            self._buffer.clear()

        # Done marker
        yield "data: [DONE]\n\n"

    # ── ASYNC STREAMING ──────────────────────────────────────
    async def astream_tokens(
        self,
        token_generator: AsyncIterator[str],
        formatter: Optional[Callable[[str], str]] = None,
    ) -> AsyncIterator[str]:
        """
        Stream tokens assíncrono com backpressure.
        """
        self._start_time = time.time()
        self._total_tokens = 0

        default_formatter = lambda t: f"data: {t}\n\n"
        fmt = formatter or default_formatter

        async for token in token_generator:
            self._total_tokens += 1

            if self.config.adaptive_buffer:
                self._buffer.append(token)
                if len(self._buffer) >= self.config.chunk_size or token in ".,!?;:\n":
                    chunk = "".join(self._buffer)
                    self._buffer.clear()
                    yield fmt(chunk)
                    await self._athrottle()
            else:
                yield fmt(token)
                await self._athrottle()

        if self._buffer:
            chunk = "".join(self._buffer)
            yield fmt(chunk)
            self._buffer.clear()

        yield "data: [DONE]\n\n"

    # ── THROTTLING ───────────────────────────────────────────
    def _throttle(self) -> None:
        """Delay adaptativo baseado na latência alvo."""
        if not self.config.adaptive_buffer:
            return
        now = time.time()
        if self._last_emit_time is not None:
            elapsed_ms = (now - self._last_emit_time) * 1000
            if elapsed_ms < self.config.min_latency_ms:
                time.sleep((self.config.min_latency_ms - elapsed_ms) / 1000)
        self._last_emit_time = time.time()

    async def _athrottle(self) -> None:
        if not self.config.adaptive_buffer:
            return
        now = time.time()
        if self._last_emit_time is not None:
            elapsed_ms = (now - self._last_emit_time) * 1000
            if elapsed_ms < self.config.min_latency_ms:
                await asyncio.sleep((self.config.min_latency_ms - elapsed_ms) / 1000)
        self._last_emit_time = time.time()

    # ── SSE FORMATTING ───────────────────────────────────────
    @staticmethod
    def format_sse(data: str, event: Optional[str] = None) -> str:
        """Formata dados no formato SSE."""
        if event:
            return f"event: {event}\ndata: {data}\n\n"
        return f"data: {data}\n\n"

    @staticmethod
    def format_openai_chunk(token: str, model: str = "vereda-native") -> str:
        """Formata chunk no formato OpenAI streaming."""
        import json
        chunk = {
            "id": f"vereda-{int(time.time() * 1000)}",
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model,
            "choices": [{
                "index": 0,
                "delta": {"content": token},
                "finish_reason": None,
            }],
        }
        return f"data: {json.dumps(chunk)}\n\n"

    # ── STATS ──────────────────────────────────────────────
    def get_stats(self) -> Dict[str, Any]:
        if self._start_time is None:
            return {"status": "idle"}
        elapsed = time.time() - self._start_time
        tps = self._total_tokens / max(elapsed, 0.001)
        return {
            "total_tokens": self._total_tokens,
            "elapsed_sec": round(elapsed, 2),
            "tokens_per_sec": round(tps, 2),
            "avg_latency_ms": round((elapsed * 1000) / max(self._total_tokens, 1), 2),
        }
