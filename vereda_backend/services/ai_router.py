"""
VEREDA / SYNTEXA — AI Router Service
=====================================
Orquestra requisições de IA entre AWS GPU e infra local.
Integra com o circuit breaker do core.
"""

import json
import logging
from typing import Any, AsyncGenerator, Optional

from fastapi import HTTPException
from starlette.responses import StreamingResponse

from vereda_backend.core.circuit_breaker import get_ai_router
from vereda_backend.core.config import settings

log = logging.getLogger(__name__)


class AiRouterService:
    """Serviço de alto nível para roteamento de inferência."""

    def __init__(self):
        self.router = get_ai_router()

    async def chat_completion(
        self,
        messages: list[dict],
        model: str = "syntexa-native",
        max_tokens: int = 4096,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> Any:
        """
        Roteia chat completion para AWS GPU ou Local.
        Retorna dict (não-stream) ou StreamingResponse.
        """
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
        }

        try:
            resp = await self.router.inference("/v1/chat/completions", payload, stream=stream)
        except Exception as e:
            log.error("AI Router chat_completion failed: %s", e)
            raise HTTPException(status_code=503, detail="AI inference unavailable. Queued for retry.")

        if stream:
            async def _sse_generator():
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        yield f"{line}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(_sse_generator(), media_type="text/event-stream")

        return resp.json()

    async def embeddings(
        self,
        inputs: list[str],
        model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
    ) -> list[list[float]]:
        """Gera embeddings via backend GPU ou local."""
        payload = {"model": model, "input": inputs}
        try:
            resp = await self.router.inference("/v1/embeddings", payload)
            data = resp.json()
            return [item["embedding"] for item in data.get("data", [])]
        except Exception as e:
            log.error("AI Router embeddings failed: %s", e)
            raise HTTPException(status_code=503, detail="Embeddings engine unavailable.")

    async def vision_describe(self, image_base64: str, prompt: Optional[str] = None) -> dict:
        """Análise de imagem via backend GPU."""
        payload = {"image": image_base64, "prompt": prompt or "Descreva esta imagem detalhadamente."}
        try:
            resp = await self.router.inference("/v1/vision/describe", payload)
            return resp.json()
        except Exception as e:
            log.error("AI Router vision failed: %s", e)
            raise HTTPException(status_code=503, detail="Vision engine unavailable.")

    async def voice_stt(self, audio_base64: str, filename: str = "audio.wav") -> dict:
        """Speech-to-Text via backend GPU."""
        payload = {"audio": audio_base64, "filename": filename}
        try:
            resp = await self.router.inference("/v1/voice/stt", payload)
            return resp.json()
        except Exception as e:
            log.error("AI Router STT failed: %s", e)
            raise HTTPException(status_code=503, detail="STT engine unavailable.")

    async def voice_tts(self, text: str, voice: Optional[str] = None) -> dict:
        """Text-to-Speech via backend GPU."""
        payload = {"text": text, "voice": voice}
        try:
            resp = await self.router.inference("/v1/voice/tts", payload)
            return resp.json()
        except Exception as e:
            log.error("AI Router TTS failed: %s", e)
            raise HTTPException(status_code=503, detail="TTS engine unavailable.")

    async def health(self) -> dict:
        """Retorna saúde de todos os backends."""
        aws = await self.router.health_check("aws")
        local = await self.router.health_check("local")
        return {
            "aws_gpu": aws,
            "local_ai": local,
            "fallback_active": aws["status"] != "ok" and local["status"] == "ok",
        }


# Singleton global
_router_service: Optional[AiRouterService] = None


def get_ai_router_service() -> AiRouterService:
    global _router_service
    if _router_service is None:
        _router_service = AiRouterService()
    return _router_service
