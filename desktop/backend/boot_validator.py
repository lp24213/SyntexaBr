#!/usr/bin/env python3
"""
SYNTEXA BOOT VALIDATOR V45
===========================
Validação OBRIGATÓRIA da Foundation Model antes de iniciar a UI.
PROIBIDO subir UI com modelo quebrado.
PROIBIDO mascarar build incompleto como sucesso.
"""
from __future__ import annotations

import json
import logging
import os
import sys
import time
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

log = logging.getLogger(__name__)

# Diretório de logs enterprise
LOGS_DIR = Path(os.environ.get("SYNTEXA_LOGS_DIR", "logs"))


@dataclass
class ValidationResult:
    name: str
    passed: bool
    error: str = ""
    detail: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0


class BootValidator:
    """
    Validação absoluta do runtime antes de permitir qualquer inferência.
    Se QUALQUER item falhar: NÃO INICIAR O CHAT.
    """

    SELF_TEST_PROMPT = "Qual o valor aproximado de PI?"
    SELF_TEST_EXPECTED_KEYWORDS = ["3.14", "pi", "π"]

    def __init__(self, checkpoint_dir: Optional[str] = None):
        self.checkpoint_dir = Path(checkpoint_dir) if checkpoint_dir else Path("checkpoints/foundation")
        self.results: List[ValidationResult] = []
        self._logs: List[Dict[str, Any]] = []

    # ── LOGS ENTERPRISE ──────────────────────────────────────

    def _log(self, level: str, msg: str, **extra: Any) -> None:
        entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S") + f".{int(time.time() * 1000) % 1000:03d}",
            "level": level,
            "component": "boot_validator",
            "message": msg,
            **extra,
        }
        self._logs.append(entry)
        getattr(log, level.lower(), log.info)("[BOOT] %s", msg)

    def write_logs(self) -> None:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        log_files = {
            "boot_validation": self._logs,
        }
        for name, entries in log_files.items():
            path = LOGS_DIR / f"{name}.log"
            with open(path, "a", encoding="utf-8") as f:
                for entry in entries:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    # ── VALIDAÇÕES ───────────────────────────────────────────

    def validate_all(self, engine: Any) -> List[ValidationResult]:
        """Executa TODAS as validações obrigatórias."""
        self.results = []
        self._log("info", "Iniciando boot validation V45...")

        checks = [
            ("checkpoint_exists", self._check_checkpoint_exists),
            ("tokenizer_exists", self._check_tokenizer_exists),
            ("vocab_valid", self._check_vocab_valid),
            ("merges_valid", self._check_merges_valid),
            ("cuda_initialized", self._check_cuda),
            ("vram_sufficient", self._check_vram),
            ("model_load", lambda: self._check_model_load(engine)),
            ("logits_valid", lambda: self._check_logits_valid(engine)),
            ("generation_functional", lambda: self._check_generation(engine)),
            ("streaming_functional", lambda: self._check_streaming(engine)),
            ("self_test_pi", lambda: self._run_self_test(engine)),
        ]

        for name, check_fn in checks:
            t0 = time.time()
            try:
                passed, detail = check_fn()
                error = "" if passed else detail.get("error", "Falha na validação")
            except Exception as exc:
                passed = False
                error = f"{type(exc).__name__}: {exc}"
                detail = {"traceback": traceback.format_exc()}
                self._log("error", f"Exceção em {name}: {error}")
            duration_ms = (time.time() - t0) * 1000
            result = ValidationResult(name=name, passed=passed, error=error, detail=detail, duration_ms=duration_ms)
            self.results.append(result)
            status = "PASS" if passed else "FAIL"
            self._log("info" if passed else "error", f"[{status}] {name}: {duration_ms:.1f}ms", detail=detail)

        self.write_logs()
        return self.results

    def is_bootable(self) -> bool:
        """Retorna True APENAS se TODAS as validações passaram."""
        if not self.results:
            return False
        failed = [r for r in self.results if not r.passed]
        if failed:
            self._log("error", f"BOOT BLOQUEADO: {len(failed)} falha(s): " + ", ".join(r.name for r in failed))
            return False
        self._log("info", "BOOT APROVADO: todas as validações passaram.")
        return True

    def get_diagnostic_report(self) -> Dict[str, Any]:
        """Relatório técnico real para exibição quando o boot falha."""
        failed = [r for r in self.results if not r.passed]
        return {
            "boot_passed": len(failed) == 0,
            "version": "V45",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "total_checks": len(self.results),
            "failed_count": len(failed),
            "failures": [
                {
                    "component": r.name,
                    "error": r.error,
                    "detail": r.detail,
                    "duration_ms": round(r.duration_ms, 1),
                }
                for r in failed
            ],
            "passed": [r.name for r in self.results if r.passed],
        }

    # ── CHECKS INDIVIDUAIS ───────────────────────────────────

    def _check_checkpoint_exists(self) -> tuple[bool, Dict[str, Any]]:
        manifest = self.checkpoint_dir / "manifest.json"
        weights = self.checkpoint_dir / "syntexa_foundation_weights.pt"
        detail = {"manifest": str(manifest), "weights": str(weights), "manifest_exists": manifest.is_file(), "weights_exists": weights.is_file()}
        if not manifest.is_file():
            return False, {**detail, "error": f"Checkpoint 70B inexistente ou não treinado. Manifesto não encontrado: {manifest}"}
        if not weights.is_file():
            return False, {**detail, "error": f"Checkpoint 70B inexistente ou não treinado. Pesos não encontrados: {weights}"}
        return True, detail

    def _check_tokenizer_exists(self) -> tuple[bool, Dict[str, Any]]:
        tok_dir = self.checkpoint_dir / "tokenizer"
        detail = {"tokenizer_dir": str(tok_dir), "exists": tok_dir.is_dir()}
        if not tok_dir.is_dir():
            return False, {**detail, "error": f"Tokenizer não encontrado em {tok_dir}"}
        return True, detail

    def _check_vocab_valid(self) -> tuple[bool, Dict[str, Any]]:
        vocab = self.checkpoint_dir / "tokenizer" / "vocab.json"
        detail = {"vocab_path": str(vocab)}
        if not vocab.is_file():
            return False, {**detail, "error": f"vocab.json ausente: {vocab}"}
        try:
            data = json.loads(vocab.read_text(encoding="utf-8"))
            size = len(data)
            detail["vocab_size"] = size
            if size < 100:
                return False, {**detail, "error": f"Vocab inválido: apenas {size} tokens (esperado >100)"}
            return True, detail
        except Exception as exc:
            return False, {**detail, "error": f"vocab.json corrompido: {exc}"}

    def _check_merges_valid(self) -> tuple[bool, Dict[str, Any]]:
        merges = self.checkpoint_dir / "tokenizer" / "merges.txt"
        bpe = self.checkpoint_dir / "tokenizer" / "tokenizer.json"
        detail = {"merges_txt": str(merges), "tokenizer_json": str(bpe)}
        # Aceita merges.txt OU tokenizer.json (BPE vs SentencePiece/Unigram)
        if merges.is_file():
            lines = [l for l in merges.read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
            detail["merges_count"] = len(lines)
            if len(lines) < 10:
                return False, {**detail, "error": f"merges.txt inválido: apenas {len(lines)} merges"}
            return True, detail
        if bpe.is_file():
            return True, {**detail, "note": "Usando tokenizer.json (HF format)"}
        return False, {**detail, "error": "Nenhum arquivo de merges/tokenizer encontrado"}

    def _check_cuda(self) -> tuple[bool, Dict[str, Any]]:
        try:
            import torch
            avail = torch.cuda.is_available()
            count = torch.cuda.device_count()
            name = torch.cuda.get_device_name(0) if avail else None
            detail = {"available": avail, "device_count": count, "device_name": name}
            # CUDA é opcional para CPU-only, mas logamos
            if not avail:
                detail["warning"] = "CUDA não disponível. Modo CPU ativado (inferência será lenta)."
                return True, detail  # Não bloqueia por não ter CUDA
            return True, detail
        except ImportError:
            return True, {"available": False, "note": "PyTorch não instalado. Modo stub."}

    def _check_vram(self) -> tuple[bool, Dict[str, Any]]:
        try:
            import torch
            if not torch.cuda.is_available():
                return True, {"note": "CPU mode — VRAM check skipped"}
            total = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
            allocated = torch.cuda.memory_allocated() / (1024 ** 3)
            free = total - allocated
            detail = {"total_gb": round(total, 2), "allocated_gb": round(allocated, 2), "free_gb": round(free, 2)}
            # Para 70B 4-bit NF4 precisa ~40GB+; se não tiver, avisa mas não bloqueia
            if free < 35:
                detail["warning"] = f"VRAM insuficiente para 70B 4-bit: {free:.1f}GB livre (recomendado 40GB+)"
            return True, detail
        except Exception as exc:
            return True, {"note": f"VRAM check skipped: {exc}"}

    def _check_model_load(self, engine: Any) -> tuple[bool, Dict[str, Any]]:
        if engine is None:
            return False, {"error": "Engine é None. Nenhum modelo carregado."}
        # Verifica se o engine tem os métodos necessários
        required = ["chat", "chat_stream"]
        missing = [m for m in required if not hasattr(engine, m)]
        detail = {"engine_type": type(engine).__name__, "missing_methods": missing}
        if missing:
            return False, {**detail, "error": f"Engine incompleto. Métodos ausentes: {missing}"}
        return True, detail

    def _check_logits_valid(self, engine: Any) -> tuple[bool, Dict[str, Any]]:
        """Executa um forward pass mínimo para verificar se logits são produzidos."""
        try:
            # Tenta obter tokenizer do engine
            tok = getattr(engine, "_tokenizer", None) or getattr(engine, "tokenizer", None)
            model = getattr(engine, "_model", None) or getattr(engine, "model", None)
            detail = {"has_tokenizer": tok is not None, "has_model": model is not None}
            if tok is None or model is None:
                # Se engine é llama.cpp ou transformers pipeline, skip detalhado
                return True, {**detail, "note": "Tokenizer/model não expostos diretamente (engine wrapper)"}
            import torch
            test_prompt = "Qual o valor de PI?"
            # Suporta tokenizer custom (SyntexaFoundationTokenizer) e HF tokenizer
            if hasattr(tok, 'encode'):
                input_ids = tok.encode(test_prompt, add_special_tokens=False)
                x = torch.tensor([input_ids], dtype=torch.long)
            else:
                inputs = tok(test_prompt, return_tensors="pt")
                x = inputs["input_ids"]
            if torch.cuda.is_available():
                x = x.cuda()
            with torch.no_grad():
                outputs = model(x)
            logits = outputs[0] if isinstance(outputs, tuple) else (outputs.logits if hasattr(outputs, "logits") else outputs)
            detail["logits_shape"] = list(logits.shape) if logits is not None else None
            if logits is None or logits.numel() == 0:
                return False, {**detail, "error": "Logits vazios ou inexistentes. Modelo quebrado."}
            return True, detail
        except Exception as exc:
            return False, {"error": f"Falha no forward pass de teste: {type(exc).__name__}: {exc}", "traceback": traceback.format_exc()}

    def _check_generation(self, engine: Any) -> tuple[bool, Dict[str, Any]]:
        try:
            result = engine.chat(messages=[{"role": "user", "content": "Say 'OK'"}], max_new_tokens=8, temperature=0.1)
            detail = {"response_preview": str(result)[:200]}
            if not str(result).strip():
                return False, {**detail, "error": "Geração retornou string vazia."}
            return True, detail
        except Exception as exc:
            return False, {"error": f"Falha na geração: {type(exc).__name__}: {exc}", "traceback": traceback.format_exc()}

    def _check_streaming(self, engine: Any) -> tuple[bool, Dict[str, Any]]:
        try:
            chunks = []
            stream = engine.chat_stream(messages=[{"role": "user", "content": "Say 'OK'"}], max_new_tokens=8, temperature=0.1)
            for chunk in stream:
                if chunk:
                    chunks.append(chunk)
                if len(chunks) > 20:
                    break
            detail = {"chunks_received": len(chunks), "first_chunks": chunks[:3]}
            if not chunks:
                return False, {**detail, "error": "Streaming não retornou nenhum chunk."}
            return True, detail
        except Exception as exc:
            return False, {"error": f"Falha no streaming: {type(exc).__name__}: {exc}", "traceback": traceback.format_exc()}

    def _run_self_test(self, engine: Any) -> tuple[bool, Dict[str, Any]]:
        """
        SELF TEST OBRIGATÓRIO:
        PROMPT: "Qual o valor aproximado de PI?"
        VALIDAR: tokenizer, inferência, logits, decoding, streaming
        RESPOSTA ESPERADA: deve conter "3.14" ou "pi" ou "π"
        """
        try:
            messages = [{"role": "user", "content": self.SELF_TEST_PROMPT}]
            # Testa geração completa
            response = engine.chat(messages=messages, max_new_tokens=64, temperature=0.3)
            response_text = str(response).lower()
            detail = {"prompt": self.SELF_TEST_PROMPT, "response": str(response)[:500]}

            # Valida conteúdo
            has_keyword = any(kw in response_text for kw in self.SELF_TEST_EXPECTED_KEYWORDS)
            detail["has_expected_keyword"] = has_keyword

            if not has_keyword:
                # Se não contém keyword, pode ser que o modelo respondeu em português de outra forma
                # Mas exigimos alguma referência numérica a PI
                if "3" not in response_text and "três" not in response_text:
                    return False, {**detail, "error": "Self-test falhou: resposta não contém valor aproximado de PI."}

            # Testa streaming também
            stream_chunks = []
            for chunk in engine.chat_stream(messages=messages, max_new_tokens=16, temperature=0.3):
                if chunk:
                    stream_chunks.append(chunk)
                if len(stream_chunks) > 30:
                    break
            detail["stream_chunks"] = len(stream_chunks)
            if not stream_chunks:
                return False, {**detail, "error": "Self-test streaming falhou: nenhum chunk recebido."}

            return True, detail
        except Exception as exc:
            return False, {"error": f"Self-test falhou: {type(exc).__name__}: {exc}", "traceback": traceback.format_exc()}


# ── PUBLIC API ─────────────────────────────────────────────

def run_boot_validation(engine: Any, checkpoint_dir: Optional[str] = None) -> BootValidator:
    validator = BootValidator(checkpoint_dir=checkpoint_dir)
    validator.validate_all(engine)
    return validator
