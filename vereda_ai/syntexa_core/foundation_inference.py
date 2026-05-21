"""
SYNTEXA FOUNDATION INFERENCE ENGINE
===================================
Motor de inferência 100% soberano.
Sem dependência de transformers, vLLM, OpenAI, Anthropic, Gemini.
Suporta: KV cache, streaming real token-by-token, batch inference,
sampling (top-k, top-p, temperature, repetition penalty).
"""
from __future__ import annotations

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Iterator, List, Optional, Tuple

import torch
import torch.nn.functional as F

from vereda_ai.syntexa_core.foundation_model import SyntexaFoundationModel, SyntexaFoundationConfig
from vereda_ai.syntexa_core.foundation_tokenizer import SyntexaFoundationTokenizer

log = logging.getLogger(__name__)

# Integração quântica opcional
try:
    import sys
    _ROOT = __file__.rsplit("vereda_ai", 1)[0]
    if _ROOT not in sys.path:
        sys.path.insert(0, _ROOT)
    from llm_quantum.hybrid_quantum_runtime import HybridQuantumRuntime
    QUANTUM_AVAILABLE = True
except Exception:
    QUANTUM_AVAILABLE = False
    HybridQuantumRuntime = None  # type: ignore[misc,assignment]


class SyntexaInferenceEngine:
    """
    Motor de inferência soberano da Syntexa Foundation Model.
    """

    def __init__(
        self,
        model: Optional[SyntexaFoundationModel] = None,
        tokenizer: Optional[SyntexaFoundationTokenizer] = None,
        device: Optional[str] = None,
        dtype: torch.dtype = torch.float32,
    ):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.dtype = dtype
        self._model = model
        self._tokenizer = tokenizer
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._quantum_runtime: Optional[Any] = None
        if QUANTUM_AVAILABLE and HybridQuantumRuntime is not None:
            try:
                self._quantum_runtime = HybridQuantumRuntime(n_qubits=8, use_quantum=True)
                log.info("[InferenceEngine] HybridQuantumRuntime integrado")
            except Exception as e:
                log.warning("[InferenceEngine] Quantum runtime não disponível: %s", e)

        self._stats: Dict[str, Any] = {
            "requests": 0,
            "tokens_generated": 0,
            "avg_latency_ms": 0.0,
            "throughput_tok_per_sec": 0.0,
            "quantum_enhanced": False,
        }

    def is_ready(self) -> bool:
        return self._model is not None and self._tokenizer is not None

    def load_from_checkpoint(
        self,
        checkpoint_path: str,
        tokenizer_dir: str,
        config: Optional[SyntexaFoundationConfig] = None,
    ) -> None:
        """Carrega modelo e tokenizer a partir de checkpoint PyTorch."""
        log.info("[InferenceEngine] Carregando tokenizer de %s", tokenizer_dir)
        self._tokenizer = SyntexaFoundationTokenizer.load(tokenizer_dir)

        log.info("[InferenceEngine] Carregando checkpoint de %s", checkpoint_path)
        payload = torch.load(checkpoint_path, map_location=self.device)
        if isinstance(payload, dict) and "model_state" in payload:
            state = payload["model_state"]
            cfg = config or SyntexaFoundationConfig(**(payload.get("config") or {}))
        else:
            state = payload
            cfg = config or SyntexaFoundationConfig()
        self._model = SyntexaFoundationModel(cfg).to(self.device).to(self.dtype)
        self._model.load_state_dict(state, strict=False)
        self._model.eval()
        log.info("[InferenceEngine] Modelo carregado: %s params", f"{sum(p.numel() for p in self._model.parameters()):,}")

    def load_from_objects(
        self,
        model: SyntexaFoundationModel,
        tokenizer: SyntexaFoundationTokenizer,
    ) -> None:
        self._model = model.to(self.device).to(self.dtype).eval()
        self._tokenizer = tokenizer

    # ── FORMATTERS ──────────────────────────────────────────────

    @staticmethod
    def format_chat_prompt(messages: List[Dict[str, str]]) -> str:
        """Converte mensagens no formato ChatML simplificado."""
        parts: list[str] = []
        for m in messages:
            role = (m.get("role") or "user").lower()
            content = (m.get("content") or "").strip()
            if role == "system":
                parts.append(f"<|system|>\n{content}")
            elif role == "user":
                parts.append(f"<|user|>\n{content}")
            elif role == "assistant":
                parts.append(f"<|assistant|>\n{content}")
        parts.append("<|assistant|>\n")
        return "\n".join(parts)

    # ── CORE GENERATION ─────────────────────────────────────────

    def generate(
        self,
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_k: int = 50,
        top_p: float = 0.9,
        repetition_penalty: float = 1.1,
        stop_sequences: Optional[List[str]] = None,
    ) -> str:
        """Geração síncrona completa."""
        if not self.is_ready():
            raise RuntimeError("InferenceEngine não inicializado. Carregue modelo + tokenizer primeiro.")

        with self._lock:
            input_ids = torch.tensor(
                [self._tokenizer.encode(prompt, add_special_tokens=False)],
                dtype=torch.long,
                device=self.device,
            )
            # Garante <bos> no início se não presente
            if input_ids.shape[1] == 0 or input_ids[0, 0].item() != self._tokenizer.bos_id:
                input_ids = torch.cat([torch.tensor([[self._tokenizer.bos_id]], dtype=torch.long, device=self.device), input_ids], dim=1)
            t0 = time.time()
            output_ids = self._model.generate(
                input_ids,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_k=top_k,
                top_p=top_p,
                eos_token_id=self._tokenizer.eos_id,
                pad_token_id=self._tokenizer.pad_id,
                repetition_penalty=repetition_penalty,
            )
            latency = (time.time() - t0) * 1000
            new_tokens = output_ids.shape[1] - input_ids.shape[1]
            self._update_stats(new_tokens, latency)

            response = self._tokenizer.decode(output_ids[0].tolist(), skip_special_tokens=True)
            # Remove prompt
            prompt_text = self._tokenizer.decode(input_ids[0].tolist(), skip_special_tokens=True)
            if response.startswith(prompt_text):
                response = response[len(prompt_text):].strip()

            if stop_sequences:
                for stop in stop_sequences:
                    if stop in response:
                        response = response[:response.index(stop)]

            return response

    def generate_stream(
        self,
        prompt: str,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_k: int = 50,
        top_p: float = 0.9,
        repetition_penalty: float = 1.1,
        use_quantum: bool = False,
    ) -> Iterator[str]:
        """Geração em streaming token por token. Se use_quantum=True e QPanda disponível, usa amostragem quântica."""
        if not self.is_ready():
            raise RuntimeError("InferenceEngine não inicializado.")

        with self._lock:
            input_ids = torch.tensor(
                [self._tokenizer.encode(prompt, add_special_tokens=False)],
                dtype=torch.long,
                device=self.device,
            )
            # Garante <bos> no início se não presente
            if input_ids.shape[1] == 0 or input_ids[0, 0].item() != self._tokenizer.bos_id:
                input_ids = torch.cat([torch.tensor([[self._tokenizer.bos_id]], dtype=torch.long, device=self.device), input_ids], dim=1)
            t0 = time.time()
            generated_tokens = 0
            quantum_active = use_quantum and self._quantum_runtime is not None
            self._stats["quantum_enhanced"] = quantum_active

            if quantum_active:
                # Quantum-enhanced token-by-token generation
                past_kv: Optional[list] = None
                for step in range(max_new_tokens):
                    logits, past_kv = self._model(input_ids if past_kv is None else input_ids[:, -1:], past_key_values=past_kv)
                    logits = logits[:, -1, :]
                    if repetition_penalty != 1.0:
                        for b in range(input_ids.shape[0]):
                            for tok_id in set(input_ids[b].tolist()):
                                if logits[b, tok_id] > 0:
                                    logits[b, tok_id] /= repetition_penalty
                                else:
                                    logits[b, tok_id] *= repetition_penalty
                    # Use quantum sampling for token selection
                    token_id, meta = self._quantum_runtime.enhance_generation(
                        logits.detach().cpu().numpy()[0],
                        generation_step=step,
                    )
                    token_id = int(token_id)
                    token_str = self._tokenizer.decode([token_id], skip_special_tokens=False)
                    yield token_str
                    generated_tokens += 1
                    input_ids = torch.cat([input_ids, torch.tensor([[token_id]], device=self.device, dtype=torch.long)], dim=-1)
                    if token_id == self._tokenizer.eos_id:
                        break
            else:
                for token_id in self._model.generate_stream(
                    input_ids,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_k=top_k,
                    top_p=top_p,
                    eos_token_id=self._tokenizer.eos_id,
                    repetition_penalty=repetition_penalty,
                ):
                    generated_tokens += 1
                    token_str = self._tokenizer.decode([token_id], skip_special_tokens=False)
                    yield token_str

            latency = (time.time() - t0) * 1000
            self._update_stats(generated_tokens, latency)

    def generate_batch(
        self,
        prompts: List[str],
        max_new_tokens: int = 256,
        temperature: float = 0.7,
        top_k: int = 50,
        top_p: float = 0.9,
    ) -> List[str]:
        """Batch inference."""
        if not self.is_ready():
            raise RuntimeError("InferenceEngine não inicializado.")

        with self._lock:
            # Padding para batch
            encoded = [self._tokenizer.encode(p, add_special_tokens=True) for p in prompts]
            max_len = max(len(e) for e in encoded)
            padded = []
            for e in encoded:
                padded.append(e + [self._tokenizer.pad_id] * (max_len - len(e)))

            input_ids = torch.tensor(padded, dtype=torch.long, device=self.device)
            # Criar attention mask
            attn_mask = (input_ids != self._tokenizer.pad_id).long()

            results: list[str] = []
            for i in range(len(prompts)):
                # Geração individual (simplificada; batch paralelo requer mais cuidado com padding)
                single_ids = input_ids[i:i+1]
                out = self._model.generate(
                    single_ids,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_k=top_k,
                    top_p=top_p,
                    eos_token_id=self._tokenizer.eos_id,
                    pad_token_id=self._tokenizer.pad_id,
                )
                prompt_len = attn_mask[i].sum().item()
                resp_ids = out[0, prompt_len:].tolist()
                text = self._tokenizer.decode(resp_ids, skip_special_tokens=True)
                results.append(text.strip())
            return results

    # ── CHAT ──────────────────────────────────────────────────

    def chat(
        self,
        messages: List[Dict[str, str]],
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_k: int = 50,
        top_p: float = 0.9,
        repetition_penalty: float = 1.1,
    ) -> str:
        prompt = self.format_chat_prompt(messages)
        return self.generate(
            prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
        )

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_k: int = 50,
        top_p: float = 0.9,
        repetition_penalty: float = 1.1,
    ) -> Iterator[str]:
        prompt = self.format_chat_prompt(messages)
        yield from self.generate_stream(
            prompt,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_k=top_k,
            top_p=top_p,
            repetition_penalty=repetition_penalty,
        )

    # ── METRICS ─────────────────────────────────────────────────

    def _update_stats(self, tokens: int, latency_ms: float) -> None:
        self._stats["requests"] += 1
        self._stats["tokens_generated"] += tokens
        n = self._stats["requests"]
        self._stats["avg_latency_ms"] = (self._stats["avg_latency_ms"] * (n - 1) + latency_ms) / n
        if latency_ms > 0:
            tps = (tokens / latency_ms) * 1000
            self._stats["throughput_tok_per_sec"] = (self._stats["throughput_tok_per_sec"] * (n - 1) + tps) / n

    def get_stats(self) -> Dict[str, Any]:
        stats = dict(self._stats)
        if torch.cuda.is_available():
            stats["vram_used_mb"] = round(torch.cuda.memory_allocated() / (1024 ** 2), 1)
            stats["vram_total_mb"] = round(torch.cuda.get_device_properties(0).total_memory / (1024 ** 2), 1)
        else:
            stats["vram_used_mb"] = 0.0
            stats["vram_total_mb"] = 0.0
        stats["device"] = self.device
        return stats

    def estimate_tokens(self, text: str) -> int:
        if self._tokenizer is None:
            raise RuntimeError("Tokenizer não carregado.")
        return len(self._tokenizer.encode(text, add_special_tokens=False))

    def shutdown(self) -> None:
        self._executor.shutdown(wait=True)
        if self._model is not None:
            del self._model
            self._model = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        log.info("[InferenceEngine] Shutdown completo.")


# ── SINGLETON / UTILS ────────────────────────────────────────

_engine: Optional[SyntexaInferenceEngine] = None
_engine_lock = threading.Lock()


def get_engine() -> SyntexaInferenceEngine:
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = SyntexaInferenceEngine()
    return _engine


def is_inference_available() -> bool:
    try:
        return get_engine().is_ready()
    except Exception:
        return False
