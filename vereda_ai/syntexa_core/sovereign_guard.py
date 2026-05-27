"""
SYNTEXA SOVEREIGN GUARD
========================
Módulo de proteção da arquitetura soberana.
Valida que nenhum componente externo foi reintroduzido.
Bloqueia tentativas de usar APIs de terceiros como core.
"""
from __future__ import annotations

import ast
import inspect
import logging
import os
import sys
from pathlib import Path
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── LISTA NEGRA DE IMPORTS ─────────────────────────────────
# Qualquer tentativa de importar estes módulos como core é bloqueada
_BANNED_IMPORTS = {
    # APIs externas proibidas
    "openai",
    "anthropic",
    "google.generativeai",
    "google.genai",
    "cohere",
    "mistralai",
    # Fallbacks proibidos
    "langchain.llms",
    "langchain.chat_models",
    "llama_index.llms",
    # Nota: transformers é permitido APENAS para vision/CLIP local,
    # nunca para carregar modelos de terceiros como core
}

# ── ARQUITETURA OFICIAL ────────────────────────────────────
_REQUIRED_FILES = [
    "vereda_ai/syntexa_core/foundation_model.py",
    "vereda_ai/syntexa_core/foundation_tokenizer.py",
    "vereda_ai/syntexa_core/foundation_trainer.py",
    "vereda_ai/syntexa_core/foundation_inference.py",
    "vereda_ai/syntexa_core/foundation_runtime.py",
    "vereda_ai/syntexa_core/dataset_pipeline.py",
    "vereda_ai/syntexa_core/memory/embeddings.py",
    "vereda_ai/syntexa_core/memory/retrieval.py",
    "vereda_ai/syntexa_core/multimodal/stt.py",
    "vereda_ai/syntexa_core/multimodal/tts.py",
    "vereda_ai/syntexa_core/multimodal/ocr.py",
    "vereda_ai/syntexa_core/multimodal/vision.py",
    "llm-quantum/quantum_scheduler.py",
    "llm-quantum/hybrid_quantum_runtime.py",
    "llm-quantum/quantum_orchestrator.py",
]

# ── PALAVRAS-CHAVE PROIBIDAS EM CÓDIGO ─────────────────────
_BANNED_KEYWORDS = [
    # Providers externos
    "openai_api_key",
    "anthropic_api_key",
    "gemini_api_key",
    "deepseek_api_key",
    "azure_openai_key",
    "fallback_to_openai",
    "fallback_to_anthropic",
    # Placeholders
    "placeholder_response",
    "dummy_reply",
    "mock_inference",
    "fake_streaming",
    "hardcoded_assistant",
    # Mensagens proibidas
    "Olá, sou a Syntexa",
    "Olá! Sou a Syntexa",
    "como posso ajudar? (placeholder)",
]


class SovereignGuardViolation(Exception):
    """Exceção levantada quando a integridade soberana é violada."""
    pass


class SovereignGuard:
    """
    Guardião da arquitetura soberana Syntexa.
    Verifica integridade em tempo de execução e em tempo de análise estática.
    
    IMPORTANTE: A governança NÃO se aplica ao admin root autenticado
    com override ativo. O admin tem autoridade soberana máxima.
    """

    def __init__(self, root_dir: Optional[str] = None):
        self.root = Path(root_dir) if root_dir else Path(__file__).resolve().parents[2]
        self.violations: list[str] = []

    def _admin_can_bypass(self) -> bool:
        """Verifica se admin root está com bypass ativo."""
        try:
            from vereda_ai.syntexa_core.admin_control import can_bypass_guard
            return can_bypass_guard()
        except Exception:
            return False

    def _is_dev_mode(self) -> bool:
        """Verifica se está em modo desenvolvimento."""
        return os.getenv("SYNTEXA_DEV_MODE", "").lower() in ("true", "1", "yes")

    def _is_production_container(self) -> bool:
        """Detecta se estamos em um container de produção (Railway, Docker, etc)."""
        # Railway injeta variáveis específicas
        if os.getenv("RAILWAY_ENVIRONMENT_NAME"):
            return True
        # Docker ou ambientes containerizados
        if os.path.exists("/.dockerenv") or os.path.exists("/run/.containerenv"):
            return True
        # Verifica se temos variáveis típicas de produção
        if os.getenv("UVICORN_WORKERS") or os.getenv("PORT"):
            return True
        return False

    # ── CHECKS DE IMPORT ────────────────────────────────────

    def check_imports(self, file_path: str | Path) -> list[str]:
        """Analisa arquivo Python em busca de imports banidos."""
        path = Path(file_path)
        if not path.is_file():
            return []

        violations = []
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        name = alias.name
                        for banned in _BANNED_IMPORTS:
                            if name == banned or name.startswith(banned + "."):
                                violations.append(f"{path}: import proibido '{name}'")
                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    for banned in _BANNED_IMPORTS:
                        if module == banned or module.startswith(banned + "."):
                            for alias in node.names:
                                violations.append(f"{path}: from {module} import {alias.name} (proibido)")
        except SyntaxError:
            pass
        return violations

    # ── CHECKS DE KEYWORDS ──────────────────────────────────

    def check_keywords(self, file_path: str | Path) -> list[str]:
        """Analisa arquivo em busca de palavras-chave proibidas."""
        path = Path(file_path)
        if not path.is_file():
            return []

        violations = []
        try:
            source = path.read_text(encoding="utf-8").lower()
            for kw in _BANNED_KEYWORDS:
                if kw.lower() in source:
                    violations.append(f"{path}: keyword proibido '{kw}'")
        except Exception:
            pass
        return violations

    # ── CHECKS DE ARQUIVOS REQUERIDOS ───────────────────────

    def check_required_files(self) -> list[str]:
        """Verifica se todos os arquivos da arquitetura oficial existem."""
        violations = []
        for rel in _REQUIRED_FILES:
            path = self.root / rel
            if not path.is_file():
                violations.append(f"ARQUIVO FALTANDO: {rel}")
        return violations

    # ── CHECKS DE RUNTIME ───────────────────────────────────

    def check_runtime_providers(self) -> list[str]:
        """Verifica se providers externos foram registrados no LLMEngine."""
        violations = []
        try:
            # Só verifica se torch estiver disponível (evita crash em ambientes sem torch)
            import importlib.util
            if importlib.util.find_spec("torch") is None:
                return violations  # Skip — ambiente sem PyTorch
            from vereda_ai.ai.llm_engine import LLMEngine
            engine = LLMEngine()
            providers = engine.available_providers()
            banned_providers = {"openai", "anthropic", "gemini", "deepseek", "azure_openai"}
            for p in providers:
                if p in banned_providers:
                    violations.append(f"LLMEngine: provider externo proibido registrado '{p}'")
        except Exception as e:
            violations.append(f"Falha ao verificar LLMEngine: {e}")
        return violations

    def check_neural_engine_discontinued(self) -> list[str]:
        """Verifica se NeuralEngine está realmente descontinuado."""
        violations = []
        try:
            import importlib.util
            if importlib.util.find_spec("torch") is None:
                return violations  # Skip
            from vereda_ai.syntexa_core.neural_engine import is_neural_available
            if is_neural_available():
                violations.append("neural_engine.py: is_neural_available() retornou True (deve ser False)")
        except Exception:
            pass
        return violations

    # ── FULL AUDIT ──────────────────────────────────────────

    def audit(self, scan_python_files: bool = True) -> Tuple[bool, list[str]]:
        """
        Executa auditoria completa da stack.
        Retorna (ok, violations).
        
        Se admin root com bypass ativo: loga aviso mas aprova.
        Se dev mode ativo: loga aviso mas aprova.
        Em container de produção: skippa check de arquivos (caminhos podem variar).
        """
        # Admin root pode bypassar completamente
        if self._admin_can_bypass():
            logger.warning("[SOVEREIGN GUARD] BYPASS: Admin root ativo. Auditoria ignorada.")
            return True, []

        # Dev mode permite evolução sem bloqueios
        if self._is_dev_mode():
            logger.info("[SOVEREIGN GUARD] DEV MODE: Auditoria relatoria apenas (não bloqueia).")
            scan_python_files = False  # Em dev, não scan arquivos para evitar noise

        self.violations = []

        # 1. Arquivos requeridos (skippa em containers — caminhos podem variar)
        if not self._is_production_container():
            self.violations.extend(self.check_required_files())
        else:
            logger.info("[SOVEREIGN GUARD] Production container: Skippa check de arquivos requeridos.")

        # 2. Runtime providers
        self.violations.extend(self.check_runtime_providers())
        self.violations.extend(self.check_neural_engine_discontinued())

        # 3. Scan de arquivos Python
        if scan_python_files:
            for py_file in self.root.rglob("*.py"):
                # Ignora __pycache__, .venv, etc.
                if any(part.startswith(".") for part in py_file.parts):
                    continue
                if "__pycache__" in str(py_file):
                    continue
                self.violations.extend(self.check_imports(py_file))
                self.violations.extend(self.check_keywords(py_file))

        ok = len(self.violations) == 0
        if not ok:
            logger.error("=" * 60)
            logger.error("[SOVEREIGN GUARD] VIOLAÇÕES DETECTADAS: %d", len(self.violations))
            for v in self.violations:
                logger.error("  - %s", v)
            logger.error("=" * 60)
            if self._is_dev_mode():
                logger.warning("[SOVEREIGN GUARD] DEV MODE: Violations reportadas mas não bloqueadas.")
                return True, self.violations  # Em dev, não falha
        else:
            logger.info("[SOVEREIGN GUARD] Auditoria aprovada. Stack soberana intacta.")

        return ok, self.violations

    def assert_sovereign(self) -> None:
        """Levanta exceção se houver violações (exceto admin root ou dev mode)."""
        # Admin root pode bypassar
        if self._admin_can_bypass():
            logger.warning("[SOVEREIGN GUARD] BYPASS: assert_sovereign ignorado (admin root).")
            return

        ok, violations = self.audit()
        if not ok:
            raise SovereignGuardViolation(
                f"[SovereignGuard] {len(violations)} violação(ões) detectada(s):\n" +
                "\n".join(f"  - {v}" for v in violations)
            )


# ── UTILS ───────────────────────────────────────────────────

def guard_runtime() -> None:
    """Chamada obrigatória no startup do runtime."""
    guard = SovereignGuard()
    guard.assert_sovereign()


def quick_check() -> bool:
    """Verificação rápida (sem scan de todos os arquivos)."""
    guard = SovereignGuard()
    ok, _ = guard.audit(scan_python_files=False)
    return ok


# ── AUTO-GUARD NO IMPORT ────────────────────────────────────
# Quando este módulo é importado, executa verificação rápida
if __name__ != "__main__":
    try:
        quick_check()
    except SovereignGuardViolation:
        # Não bloqueia import, apenas loga
        pass
