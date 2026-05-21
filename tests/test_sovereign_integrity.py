"""
SYNTEXA SOVEREIGN INTEGRITY TESTS
===================================
Testes que FALHAM se qualquer componente da arquitetura soberana
for removido, simplificado, ou se APIs externas forem reintroduzidas.

Estes testes existem para PROTEGER a stack de regressões.
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

# Caminhos
ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "vereda_ai" / "syntexa_core"
QUANTUM = ROOT / "llm-quantum"


class TestArchitectureExists:
    """Verifica se todos os arquivos da arquitetura oficial existem."""

    REQUIRED_FILES = [
        CORE / "foundation_model.py",
        CORE / "foundation_tokenizer.py",
        CORE / "foundation_trainer.py",
        CORE / "foundation_inference.py",
        CORE / "foundation_runtime.py",
        CORE / "dataset_pipeline.py",
        CORE / "memory" / "embeddings.py",
        CORE / "memory" / "retrieval.py",
        CORE / "multimodal" / "stt.py",
        CORE / "multimodal" / "tts.py",
        CORE / "multimodal" / "ocr.py",
        CORE / "multimodal" / "vision.py",
        QUANTUM / "quantum_scheduler.py",
        QUANTUM / "hybrid_quantum_runtime.py",
        QUANTUM / "quantum_orchestrator.py",
    ]

    def test_all_required_files_exist(self):
        missing = [str(f.relative_to(ROOT)) for f in self.REQUIRED_FILES if not f.is_file()]
        assert not missing, f"Arquivos faltando da arquitetura soberana: {missing}"


class TestNoExternalProviders:
    """Verifica que nenhum provider externo foi reintroduzido."""

    def test_llm_engine_has_only_sovereign_providers(self):
        from vereda_ai.ai.llm_engine import LLMEngine
        engine = LLMEngine()
        providers = engine.available_providers()
        banned = {"openai", "anthropic", "gemini", "deepseek", "azure_openai", "ollama"}
        found = [p for p in providers if p in banned]
        assert not found, f"Providers externos proibidos encontrados: {found}"

    def test_default_provider_is_sovereign(self):
        from vereda_ai.ai.llm_engine import LLMEngine
        engine = LLMEngine()
        default = engine.default_provider()
        assert default == "syntexa_native", f"Default deve ser 'syntexa_native', mas é '{default}'"


class TestNeuralEngineDiscontinued:
    """Verifica que o NeuralEngine legado está descontinuado."""

    def test_is_neural_available_returns_false(self):
        from vereda_ai.syntexa_core.neural_engine import is_neural_available
        assert is_neural_available() is False, "is_neural_available() deve retornar False"

    def test_neural_engine_raises_on_init(self):
        from vereda_ai.syntexa_core.neural_engine import NeuralEngine
        with pytest.raises(RuntimeError, match="descontinuado"):
            NeuralEngine()


class TestNoBannedImports:
    """Verifica que não há imports de APIs externas banidas."""

    BANNED_IMPORTS = {
        "openai",
        "anthropic",
        "google.generativeai",
        "cohere",
        "mistralai",
    }

    def test_no_banned_imports_in_core(self):
        violations = []
        for py_file in CORE.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            source = py_file.read_text(encoding="utf-8")
            try:
                tree = ast.parse(source)
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name in self.BANNED_IMPORTS:
                            violations.append(f"{py_file}: import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    if node.module in self.BANNED_IMPORTS:
                        violations.append(f"{py_file}: from {node.module}")

        assert not violations, f"Imports proibidos encontrados:\n" + "\n".join(violations)


class TestNoBannedKeywords:
    """Verifica que não há keywords proibidas no código."""

    BANNED_KEYWORDS = [
        "fallback_to_openai",
        "fallback_to_anthropic",
        "placeholder_response",
        "dummy_reply",
        "mock_inference",
        "fake_streaming",
    ]

    def test_no_banned_keywords_in_core(self):
        violations = []
        for py_file in CORE.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            source = py_file.read_text(encoding="utf-8").lower()
            for kw in self.BANNED_KEYWORDS:
                if kw.lower() in source:
                    violations.append(f"{py_file}: keyword '{kw}'")

        assert not violations, f"Keywords proibidas encontradas:\n" + "\n".join(violations)


class TestFoundationModelArchitecture:
    """Verifica que a Foundation Model mantém arquitetura correta."""

    def test_model_has_rope(self):
        source = (CORE / "foundation_model.py").read_text(encoding="utf-8")
        assert "RoPE" in source or "rope" in source.lower(), "FoundationModel deve ter RoPE"

    def test_model_has_rmsnorm(self):
        source = (CORE / "foundation_model.py").read_text(encoding="utf-8")
        assert "RMSNorm" in source, "FoundationModel deve ter RMSNorm"

    def test_model_has_swiglu(self):
        source = (CORE / "foundation_model.py").read_text(encoding="utf-8")
        assert "SwiGLU" in source, "FoundationModel deve ter SwiGLU"

    def test_model_has_gqa(self):
        source = (CORE / "foundation_model.py").read_text(encoding="utf-8")
        assert "GQA" in source or "num_kv_heads" in source, "FoundationModel deve ter GQA"

    def test_model_has_kv_cache(self):
        source = (CORE / "foundation_model.py").read_text(encoding="utf-8")
        assert "kv_cache" in source.lower() or "past_key_values" in source.lower(), "FoundationModel deve ter KV Cache"


class TestQuantumLayer:
    """Verifica que a camada QPanda3 existe e tem código real."""

    def test_quantum_scheduler_exists(self):
        path = QUANTUM / "quantum_scheduler.py"
        assert path.is_file()
        source = path.read_text(encoding="utf-8")
        assert "pyqpanda" in source or "CPUQVM" in source, "QuantumScheduler deve referenciar QPanda"

    def test_hybrid_quantum_runtime_exists(self):
        path = QUANTUM / "hybrid_quantum_runtime.py"
        assert path.is_file()
        source = path.read_text(encoding="utf-8")
        assert "quantum_sample_logits" in source, "HybridQuantumRuntime deve ter quantum_sample_logits"


class TestMultimodal:
    """Verifica que o stack multimodal existe."""

    def test_stt_exists(self):
        assert (CORE / "multimodal" / "stt.py").is_file()

    def test_tts_exists(self):
        assert (CORE / "multimodal" / "tts.py").is_file()

    def test_ocr_exists(self):
        assert (CORE / "multimodal" / "ocr.py").is_file()

    def test_vision_exists(self):
        assert (CORE / "multimodal" / "vision.py").is_file()


class TestMemory:
    """Verifica que memória/RAG existe."""

    def test_embeddings_exists(self):
        assert (CORE / "memory" / "embeddings.py").is_file()

    def test_retrieval_exists(self):
        assert (CORE / "memory" / "retrieval.py").is_file()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
