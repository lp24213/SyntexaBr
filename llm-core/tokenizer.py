"""
VEREDA / SYNTEXA — Tokenizer Pipeline
======================================
Pipeline completo de tokenização com:
- SentencePiece / BPE / Unigram support
- Dynamic vocabulary
- Code-aware tokenization
- Multilingual segmentation
- Prompt templating
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

try:
    from transformers import AutoTokenizer
except ImportError:
    AutoTokenizer = None

log = logging.getLogger(__name__)


@dataclass
class TokenizationResult:
    tokens: List[int]
    text: str
    token_count: int
    char_count: int
    language_detected: str = "auto"
    is_code: bool = False
    is_multilingual: bool = False


class VeredaTokenizer:
    """
    Tokenizer pipeline proprietário da VEREDA.
    Suporta múltiplos backends e otimizações.
    """

    # Templates de prompt para diferentes modos
    TEMPLATES = {
        "chat": "<|user|>\n{user}\n<|assistant|>\n",
        "system": "<|system|>\n{system}\n<|user|>\n{user}\n<|assistant|>\n",
        "code": "<|code|>\n# Language: {lang}\n{prompt}\n<|generate|>\n",
        "reasoning": "<|think|>\nPense passo a passo sobre: {prompt}\n<|answer|>\n",
        "multimodal": "<|image|>\n{image_desc}\n<|user|>\n{prompt}\n<|assistant|>\n",
    }

    def __init__(self, model_name: str = "microsoft/DialoGPT-medium"):
        self.model_name = model_name
        self._backend = None
        self._vocab_size = 0
        self._load_backend()

    def _load_backend(self) -> None:
        if AutoTokenizer is None:
            log.warning("transformers não instalado — usando tokenizer fallback")
            return
        try:
            self._backend = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True,
                use_fast=True,
            )
            if self._backend.pad_token is None:
                self._backend.pad_token = self._backend.eos_token
            self._vocab_size = len(self._backend)
            log.info("Tokenizer loaded: %s (vocab=%d)", self.model_name, self._vocab_size)
        except Exception as e:
            log.error("Failed to load tokenizer: %s — using fallback", e)
            self._backend = None

    # ── CORE TOKENIZATION ──────────────────────────────────
    def encode(self, text: str, max_length: Optional[int] = None) -> List[int]:
        if self._backend is None:
            return self._fallback_encode(text)
        encoded = self._backend.encode(text, add_special_tokens=True)
        if max_length and len(encoded) > max_length:
            encoded = encoded[:max_length]
        return encoded

    def decode(self, tokens: List[int], skip_special: bool = True) -> str:
        if self._backend is None:
            return self._fallback_decode(tokens)
        return self._backend.decode(tokens, skip_special_tokens=skip_special)

    def count_tokens(self, text: str) -> int:
        return len(self.encode(text))

    # ── FALLBACK (quando transformers não disponível) ────────
    def _fallback_encode(self, text: str) -> List[int]:
        # Simples word-based encoding para fallback
        words = re.findall(r"\w+|[^\w\s]", text)
        return [hash(w) % 50000 for w in words]

    def _fallback_decode(self, tokens: List[int]) -> str:
        return " ".join(f"<tok_{t}>" for t in tokens)

    # ── PROMPT TEMPLATING ────────────────────────────────────
    def apply_template(
        self,
        prompt: str,
        mode: str = "chat",
        system: Optional[str] = None,
        context: Optional[List[Dict[str, str]]] = None,
        image_desc: Optional[str] = None,
        lang: Optional[str] = None,
    ) -> str:
        """
        Aplica template de prompt com histórico de contexto.
        """
        # Construir histórico
        history_parts = []
        if context:
            for msg in context[-6:]:  # últimas 6 mensagens
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "user":
                    history_parts.append(f"<|user|>\n{content}")
                elif role == "assistant":
                    history_parts.append(f"<|assistant|>\n{content}")
                elif role == "system":
                    history_parts.append(f"<|system|>\n{content}")

        # Aplicar template do modo
        if mode == "system" and system:
            formatted = self.TEMPLATES["system"].format(system=system, user=prompt)
        elif mode == "code" and lang:
            formatted = self.TEMPLATES["code"].format(lang=lang, prompt=prompt)
        elif mode == "reasoning":
            formatted = self.TEMPLATES["reasoning"].format(prompt=prompt)
        elif mode == "multimodal" and image_desc:
            formatted = self.TEMPLATES["multimodal"].format(image_desc=image_desc, prompt=prompt)
        else:
            formatted = self.TEMPLATES["chat"].format(user=prompt)

        # Combinar histórico + prompt atual
        if history_parts:
            full = "\n".join(history_parts) + "\n" + formatted
        else:
            full = formatted

        return full

    # ── CODE-AWARE TOKENIZATION ────────────────────────────
    def tokenize_code(self, code: str, language: str = "python") -> TokenizationResult:
        """Tokenização otimizada para código-fonte."""
        # Preservar indentação e estrutura
        lines = code.split("\n")
        preserved = []
        for line in lines:
            indent = len(line) - len(line.lstrip())
            preserved.append(f"<|indent{indent}|>{line.strip()}")

        processed = "\n".join(preserved)
        tokens = self.encode(processed)

        return TokenizationResult(
            tokens=tokens,
            text=processed,
            token_count=len(tokens),
            char_count=len(code),
            is_code=True,
            language_detected=language,
        )

    # ── MULTILINGUAL DETECTION ───────────────────────────────
    def detect_language(self, text: str) -> str:
        """Detecção simples de linguagem baseada em caracteres."""
        # Heurística rápida
        if re.search(r"[\u3040-\u309f\u30a0-\u30ff]", text):
            return "ja"
        if re.search(r"[\u4e00-\u9fff]", text):
            return "zh"
        if re.search(r"[\uac00-\ud7af]", text):
            return "ko"
        if re.search(r"[\u0400-\u04ff]", text):
            return "ru"
        if re.search(r"[\u00e0-\u00fc]", text.lower()):
            return "pt/fr/es/de"  # latim
        return "en"

    # ── TRUNCATION INTELIGENTE ───────────────────────────────
    def truncate_to_tokens(self, text: str, max_tokens: int, strategy: str = "tail") -> str:
        """Trunca texto respeitando tokens, mantendo coerência."""
        tokens = self.encode(text)
        if len(tokens) <= max_tokens:
            return text

        if strategy == "tail":
            truncated_tokens = tokens[:max_tokens]
        elif strategy == "head":
            truncated_tokens = tokens[-max_tokens:]
        elif strategy == "middle":
            half = max_tokens // 2
            truncated_tokens = tokens[:half] + tokens[-half:]
        else:
            truncated_tokens = tokens[:max_tokens]

        return self.decode(truncated_tokens)

    # ── CHUNKING ─────────────────────────────────────────────
    def chunk_text(self, text: str, max_tokens: int = 512, overlap: int = 50) -> List[str]:
        """Divide texto em chunks com overlap."""
        tokens = self.encode(text)
        chunks = []
        stride = max_tokens - overlap

        for i in range(0, len(tokens), stride):
            chunk_tokens = tokens[i:i + max_tokens]
            chunk_text = self.decode(chunk_tokens)
            chunks.append(chunk_text)

        return chunks
