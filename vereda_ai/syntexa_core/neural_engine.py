"""
VEREDA / SYNTEXA — Neural Engine
==================================
Motor neural completo com transformers para geração de texto real.
Modelos 20B+ parâmetros com quantização 4-bit (bitsandbytes) para rodar na AWS.
"""
from __future__ import annotations

import logging
import re
import threading
import time
from typing import Any, Iterator, Optional

logger = logging.getLogger(__name__)

# ── Lazy imports (não quebra import se transformers não estiver) ──
_transformers = None
_torch = None


def _import_transformers():
    global _transformers
    if _transformers is None:
        try:
            import transformers as _t
            _transformers = _t
        except ImportError as e:
            logger.error("transformers não instalado: %s", e)
            raise
    return _transformers


def _import_torch():
    global _torch
    if _torch is None:
        try:
            import torch as _t
            _torch = _t
        except ImportError as e:
            logger.error("torch não instalado: %s", e)
            raise
    return _torch


# ── Configuração de modelo ───────────────────────────────────────
# Modelos grandes 20B+ com quantização 4-bit para AWS
LARGE_MODELS = [
    "Qwen/Qwen2.5-32B-Instruct",              # 32B — 4-bit ~16GB VRAM
    "Qwen/Qwen2.5-14B-Instruct",               # 14B — 4-bit ~8GB VRAM (fallback)
    "microsoft/phi-4",                        # 14B SOTA
    "meta-llama/Llama-3.1-8B-Instruct",      # 8B — funciona em CPU se preciso
]

DEFAULT_MAX_NEW_TOKENS = 512
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_P = 0.9


class NeuralEngine:
    """
    Motor neural para geração de texto real com transformers.
    Lazy-loading: só carrega o modelo na primeira chamada.
    Usa quantization 4-bit via bitsandbytes para modelos grandes na AWS.
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
        top_p: float = DEFAULT_TOP_P,
        load_in_4bit: bool = True,
    ):
        self.model_name = model_name or LARGE_MODELS[0]
        self.device = device
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.load_in_4bit = load_in_4bit

        self._model: Any = None
        self._tokenizer: Any = None
        self._lock = threading.RLock()
        self._loaded = False

    # ── LOADING ──────────────────────────────────────────────
    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        with self._lock:
            if self._loaded:
                return
            self._load()
            self._loaded = True

    def _load(self) -> None:
        transformers = _import_transformers()
        torch = _import_torch()

        device = self.device or ("cuda" if torch.cuda.is_available() else "cpu")
        logger.info("[NeuralEngine] Carregando modelo: %s em %s (4bit=%s)", self.model_name, device, self.load_in_4bit)

        t0 = time.time()

        # Tokenizer
        self._tokenizer = transformers.AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=True,
        )
        if self._tokenizer.pad_token is None:
            self._tokenizer.pad_token = self._tokenizer.eos_token

        # Modelo com quantização 4-bit para caber na AWS
        load_kwargs: dict[str, Any] = {
            "trust_remote_code": True,
            "device_map": "auto" if device == "cuda" else None,
        }

        if self.load_in_4bit and device == "cuda":
            try:
                from transformers import BitsAndBytesConfig
                load_kwargs["quantization_config"] = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.float16,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_use_double_quant=True,
                )
                logger.info("[NeuralEngine] Quantização 4-bit ativada (NF4)")
            except Exception:
                load_kwargs["torch_dtype"] = torch.float16
                logger.warning("[NeuralEngine] BitsAndBytes indisponível; usando fp16")
        else:
            load_kwargs["torch_dtype"] = torch.float16 if device == "cuda" else torch.float32

        self._model = transformers.AutoModelForCausalLM.from_pretrained(
            self.model_name,
            **load_kwargs,
        )

        if device == "cpu":
            self._model = self._model.to("cpu")

        self._model.eval()
        dt = time.time() - t0
        logger.info("[NeuralEngine] Modelo carregado em %.1fs", dt)

    def is_available(self) -> bool:
        try:
            self._ensure_loaded()
            return True
        except Exception as e:
            logger.warning("[NeuralEngine] Indisponível: %s", e)
            return False

    # ── CHAT FORMAT ──────────────────────────────────────────
    def _build_prompt(self, messages: list[dict[str, Any]]) -> str:
        """Converte mensagens no formato ChatML ou template do modelo."""
        if hasattr(self._tokenizer, "apply_chat_template") and self._tokenizer.chat_template:
            try:
                return self._tokenizer.apply_chat_template(
                    messages,
                    tokenize=False,
                    add_generation_prompt=True,
                )
            except Exception:
                pass

        # Fallback: formatação manual estilo ChatML
        parts: list[str] = []
        for msg in messages:
            role = (msg.get("role") or "user").lower()
            content = (msg.get("content") or "").strip()
            if role == "system":
                parts.append(f" system\n{content} ")
            elif role == "user":
                parts.append(f" user\n{content} ")
            elif role == "assistant":
                parts.append(f" assistant\n{content} ")
        parts.append(" assistant\n")
        return "\n".join(parts)

    # ── GENERATION ───────────────────────────────────────────
    def generate(self, messages: list[dict[str, Any]], **kwargs: Any) -> str:
        self._ensure_loaded()
        torch = _import_torch()

        prompt = self._build_prompt(messages)
        inputs = self._tokenizer(prompt, return_tensors="pt", truncation=True, max_length=4096)
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}

        max_new = kwargs.get("max_new_tokens", self.max_new_tokens)
        temp = kwargs.get("temperature", self.temperature)
        top_p = kwargs.get("top_p", self.top_p)

        gen_kwargs = {
            "max_new_tokens": max_new,
            "do_sample": temp > 0,
            "temperature": max(temp, 0.01),
            "top_p": top_p,
            "pad_token_id": self._tokenizer.pad_token_id,
            "eos_token_id": self._tokenizer.eos_token_id,
        }

        t0 = time.time()
        with torch.no_grad():
            output_ids = self._model.generate(**inputs, **gen_kwargs)
        latency = (time.time() - t0) * 1000

        # Remove prompt da resposta
        prompt_len = inputs["input_ids"].shape[1]
        new_ids = output_ids[0, prompt_len:]
        response = self._tokenizer.decode(new_ids, skip_special_tokens=True).strip()

        # Limpa tags ChatML residuais
        response = re.sub(r"<\|im_end\|>.*", "", response, flags=re.S).strip()
        response = re.sub(r"<\|im_start\|>.*", "", response, flags=re.S).strip()

        new_tokens = len(new_ids)
        if latency > 0:
            logger.debug("[NeuralEngine] %d tokens em %.0fms (%.1f tok/s)", new_tokens, latency, new_tokens / (latency / 1000))
        return response

    # ── STREAMING ────────────────────────────────────────────
    def generate_stream(self, messages: list[dict[str, Any]], **kwargs: Any) -> Iterator[str]:
        self._ensure_loaded()
        torch = _import_torch()

        prompt = self._build_prompt(messages)
        inputs = self._tokenizer(prompt, return_tensors="pt", truncation=True, max_length=4096)
        if torch.cuda.is_available():
            inputs = {k: v.cuda() for k, v in inputs.items()}

        input_ids = inputs["input_ids"]
        past_key_values = None
        max_new = kwargs.get("max_new_tokens", self.max_new_tokens)
        temp = kwargs.get("temperature", self.temperature)
        top_p = kwargs.get("top_p", self.top_p)

        for _ in range(max_new):
            with torch.no_grad():
                outputs = self._model(
                    input_ids=input_ids if past_key_values is None else input_ids[:, -1:],
                    past_key_values=past_key_values,
                    use_cache=True,
                )
            logits = outputs.logits[:, -1, :]
            past_key_values = outputs.past_key_values

            # Sampling
            probs = torch.softmax(logits / max(temp, 0.01), dim=-1)
            # Top-p filtering
            sorted_probs, sorted_indices = torch.sort(probs, descending=True)
            cumsum = torch.cumsum(sorted_probs, dim=-1)
            sorted_indices_to_remove = cumsum > top_p
            sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
            sorted_indices_to_remove[..., 0] = 0
            indices_to_remove = sorted_indices[sorted_indices_to_remove]
            probs[0, indices_to_remove] = 0
            probs = probs / probs.sum()

            next_token = torch.multinomial(probs, num_samples=1)
            token_str = self._tokenizer.decode([next_token.item()], skip_special_tokens=True)

            if next_token.item() == self._tokenizer.eos_token_id:
                break

            yield token_str
            input_ids = torch.cat([input_ids, next_token], dim=-1)

    # ── SHUTDOWN ─────────────────────────────────────────────
    def shutdown(self) -> None:
        if self._model is not None:
            del self._model
            self._model = None
        if self._tokenizer is not None:
            del self._tokenizer
            self._tokenizer = None
        try:
            torch = _import_torch()
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass
        self._loaded = False


# ── Singleton ────────────────────────────────────────────────
_neural_engine: Optional[NeuralEngine] = None
_neural_lock = threading.Lock()


def get_neural_engine() -> NeuralEngine:
    global _neural_engine
    if _neural_engine is None:
        with _neural_lock:
            if _neural_engine is None:
                _neural_engine = NeuralEngine()
    return _neural_engine


def neural_generate(messages: list[dict[str, Any]], **kwargs: Any) -> str:
    """Geração síncrona via motor neural."""
    try:
        engine = get_neural_engine()
        return engine.generate(messages, **kwargs)
    except Exception as e:
        logger.error("[NeuralEngine] Falha na geração: %s", e)
        raise


def neural_generate_stream(messages: list[dict[str, Any]], **kwargs: Any) -> Iterator[str]:
    """Geração em streaming via motor neural."""
    try:
        engine = get_neural_engine()
        yield from engine.generate_stream(messages, **kwargs)
    except Exception as e:
        logger.error("[NeuralEngine] Falha no stream: %s", e)
        raise


def is_neural_available() -> bool:
    """Verifica se o motor neural pode ser carregado."""
    try:
        _import_transformers()
        _import_torch()
        return True
    except Exception:
        return False
