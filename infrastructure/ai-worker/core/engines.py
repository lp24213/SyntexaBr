"""Lazy-loaded AI engines. NENHUM modelo é carregado no import."""
from __future__ import annotations

import logging
import threading
from typing import Any

from worker.core.config import settings

logger = logging.getLogger(__name__)

# ── Locks para lazy loading thread-safe ──
_embed_lock = threading.Lock()
_llm_lock = threading.Lock()
_whisper_lock = threading.Lock()
_ocr_lock = threading.Lock()
_tts_lock = threading.Lock()

# ── Instâncias (inicialmente None) ──
_embed_model: Any = None
_embed_model_name: str | None = None
_llm_pipeline: Any = None
_whisper_model: Any = None
_ocr_reader: Any = None
_tts_engine: Any = None


# ── Embeddings ──
def get_embed_engine() -> Any:
    global _embed_model, _embed_model_name
    if _embed_model is not None:
        return _embed_model
    with _embed_lock:
        if _embed_model is not None:
            return _embed_model
        backend = (settings.embedding_backend or "fastembed").lower()
        model_name = settings.fastembed_model_name
        if backend == "fastembed":
            try:
                from fastembed import TextEmbedding
                _embed_model = TextEmbedding(model_name)
                _embed_model_name = model_name
                logger.info("FastEmbed loaded: %s", model_name)
            except Exception as exc:
                logger.error("FastEmbed failed: %s", exc)
                raise
        else:
            raise RuntimeError(f"Unsupported embedding backend: {backend}")
    return _embed_model


def embed_texts(texts: list[str]) -> list[list[float]]:
    engine = get_embed_engine()
    out: list[list[float]] = []
    for emb in engine.embed(texts):
        out.append([float(x) for x in emb])
    return out


# ── LLM Inference ──
def get_llm_pipeline() -> Any:
    global _llm_pipeline
    if _llm_pipeline is not None:
        return _llm_pipeline
    with _llm_lock:
        if _llm_pipeline is not None:
            return _llm_pipeline
        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
            model_name = settings.default_llm_model
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info("Loading LLM %s on %s...", model_name, device)
            tokenizer = AutoTokenizer.from_pretrained(model_name, token=settings.huggingface_token)
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                device_map="auto" if device == "cuda" else None,
                token=settings.huggingface_token,
            )
            _llm_pipeline = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                device=0 if device == "cuda" else -1,
            )
            logger.info("LLM loaded: %s", model_name)
        except Exception as exc:
            logger.error("LLM load failed: %s", exc)
            raise
    return _llm_pipeline


def generate_text(messages: list[dict[str, str]], *, temperature: float = 0.7, max_tokens: int = 2048) -> str:
    pipe = get_llm_pipeline()
    prompt = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
    result = pipe(
        prompt,
        max_new_tokens=max_tokens,
        temperature=temperature,
        do_sample=True,
        return_full_text=False,
    )
    return result[0]["generated_text"].strip()


# ── Whisper (STT) ──
def get_whisper_model() -> Any:
    global _whisper_model
    if _whisper_model is not None:
        return _whisper_model
    with _whisper_lock:
        if _whisper_model is not None:
            return _whisper_model
        try:
            import whisper
            size = settings.whisper_model_size
            logger.info("Loading Whisper model: %s", size)
            _whisper_model = whisper.load_model(size)
            logger.info("Whisper loaded")
        except Exception as exc:
            logger.error("Whisper load failed: %s", exc)
            raise
    return _whisper_model


def transcribe_audio(audio_path: str, language: str = "pt") -> dict[str, Any]:
    model = get_whisper_model()
    result = model.transcribe(audio_path, language=language)
    return {"text": result["text"], "language": result.get("language", language)}


# ── OCR (EasyOCR) ──
def get_ocr_reader() -> Any:
    global _ocr_reader
    if _ocr_reader is not None:
        return _ocr_reader
    with _ocr_lock:
        if _ocr_reader is not None:
            return _ocr_reader
        try:
            import easyocr
            lang = settings.ocr_language
            logger.info("Loading EasyOCR for language: %s", lang)
            _ocr_reader = easyocr.Reader([lang])
            logger.info("OCR loaded")
        except Exception as exc:
            logger.error("OCR load failed: %s", exc)
            raise
    return _ocr_reader


def ocr_image(image_bytes: bytes) -> dict[str, Any]:
    import numpy as np
    from PIL import Image
    reader = get_ocr_reader()
    img = Image.open(image_bytes)
    arr = np.array(img)
    results = reader.readtext(arr)
    texts = [r[1] for r in results]
    return {"text": " ".join(texts), "blocks": len(texts)}


# ── TTS (Edge-TTS) ──
def get_tts_engine() -> Any:
    global _tts_engine
    if _tts_engine is not None:
        return _tts_engine
    with _tts_lock:
        if _tts_engine is not None:
            return _tts_engine
        try:
            import edge_tts
            _tts_engine = edge_tts
            logger.info("Edge-TTS loaded")
        except Exception as exc:
            logger.error("TTS load failed: %s", exc)
            raise
    return _tts_engine


def generate_tts(text: str, voice: str | None = None) -> bytes:
    import asyncio
    engine = get_tts_engine()
    v = voice or settings.edge_tts_voice or "pt-BR-FranciscaNeural"

    async def _go() -> bytes:
        communicate = engine.Communicate(text, v)
        chunks: list[bytes] = []
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                chunks.append(chunk["data"])
        return b"".join(chunks)

    return asyncio.run(_go())
