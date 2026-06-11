"""
SYNTEXA FOUNDATION RUNTIME
==========================
Entrypoint de integração da Foundation Model ao ecossistema Syntexa.
Substitui / complementa o hybrid_engine e neural_engine existentes
com inferência 100% soberana, sem modelos de terceiros.
"""
from __future__ import annotations

import json
import logging
import os
import threading
from pathlib import Path
from typing import Any, Iterator, List, Optional

from vereda_ai.syntexa_core.foundation_tokenizer import SyntexaFoundationTokenizer

# Imports que dependem de torch são opcionais: no gateway leve (Railway, sem torch)
# o motor é servido via HTTP (Ollama/proxy), então a Foundation Model própria não carrega.
# Mantém comportamento idêntico onde torch existe (AWS/treino).
try:
    from vereda_ai.syntexa_core.foundation_model import SyntexaFoundationModel, SyntexaFoundationConfig
    from vereda_ai.syntexa_core.foundation_inference import SyntexaInferenceEngine
except ImportError as _torch_exc:  # torch ausente no container leve
    SyntexaFoundationModel = None  # type: ignore[assignment,misc]
    SyntexaFoundationConfig = None  # type: ignore[assignment,misc]
    SyntexaInferenceEngine = None  # type: ignore[assignment,misc]
    logging.getLogger(__name__).warning(
        "Foundation Model indisponível (torch ausente): %s. "
        "Inferência seguirá via provedor HTTP configurado.", _torch_exc
    )

logger = logging.getLogger(__name__)

_RUNTIME: Optional["SyntexaFoundationRuntime"] = None
_RUNTIME_LOCK = threading.Lock()


class SyntexaFoundationRuntime:
    """
    Runtime soberano da Foundation Model Syntexa.
    Carrega modelo + tokenizer + inference engine.
    """

    def __init__(self, checkpoint_dir: Optional[str] = None):
        if SyntexaInferenceEngine is None:
            raise RuntimeError(
                "Foundation Model indisponível: torch não está instalado neste runtime. "
                "Use um provedor HTTP (Ollama/proxy) para inferência."
            )
        self.checkpoint_dir = Path(checkpoint_dir) if checkpoint_dir else Path("checkpoints/foundation")
        self.engine = SyntexaInferenceEngine()
        self._loaded = False

    def load(self) -> bool:
        """Tenta carregar modelo do checkpoint_dir. Retorna True se sucesso."""
        if self._loaded:
            return True

        manifest = self.checkpoint_dir / "manifest.json"
        weights = self.checkpoint_dir / "syntexa_foundation_weights.pt"
        tokenizer_dir = self.checkpoint_dir / "tokenizer"

        if not manifest.is_file():
            logger.warning("[FoundationRuntime] Manifest não encontrado: %s", manifest)
            return False
        if not weights.is_file():
            logger.warning("[FoundationRuntime] Weights não encontrados: %s", weights)
            return False
        if not (tokenizer_dir / "vocab.json").is_file():
            logger.warning("[FoundationRuntime] Tokenizer não encontrado: %s", tokenizer_dir)
            return False

        try:
            cfg = None
            config_path = self.checkpoint_dir / "config.json"
            if config_path.is_file():
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg_dict = json.load(f)
                cfg_dict.pop("dtype", None)
                cfg = SyntexaFoundationConfig(**cfg_dict)
            self.engine.load_from_checkpoint(
                checkpoint_path=str(weights),
                tokenizer_dir=str(tokenizer_dir),
                config=cfg,
            )
            self._loaded = True
            logger.info("[FoundationRuntime] Modelo soberano carregado com sucesso.")
            return True
        except Exception as exc:
            logger.error("[FoundationRuntime] Falha ao carregar modelo: %s", exc)
            return False

    def load_from_objects(
        self,
        model: SyntexaFoundationModel,
        tokenizer: SyntexaFoundationTokenizer,
    ) -> None:
        self.engine.load_from_objects(model, tokenizer)
        self._loaded = True

    def is_ready(self) -> bool:
        return self._loaded and self.engine.is_ready()

    # ── CHAT INTERFACE ────────────────────────────────────────

    def chat(self, messages: List[Dict[str, str]], **kwargs: Any) -> str:
        if not self.is_ready():
            raise RuntimeError("FoundationRuntime não está pronto. Carregue o modelo primeiro.")
        return self.engine.chat(messages, **kwargs)

    def chat_stream(self, messages: List[Dict[str, str]], **kwargs: Any) -> Iterator[str]:
        if not self.is_ready():
            raise RuntimeError("FoundationRuntime não está pronto.")
        yield from self.engine.chat_stream(messages, **kwargs)

    def embed(self, texts: List[str], **kwargs: Any) -> List[List[float]]:
        """Embeddings via inference engine (se suportado no futuro) ou fallback."""
        # Por ora, delega para o sistema de embeddings existente
        from vereda_ai.syntexa_core.memory.embeddings import SyntexaEmbeddings
        emb = SyntexaEmbeddings()
        return emb.embed(texts)

    def shutdown(self) -> None:
        self.engine.shutdown()
        self._loaded = False


# ── PUBLIC API ──────────────────────────────────────────────

def get_foundation_runtime(checkpoint_dir: Optional[str] = None) -> SyntexaFoundationRuntime:
    global _RUNTIME
    if _RUNTIME is None:
        with _RUNTIME_LOCK:
            if _RUNTIME is None:
                _RUNTIME = SyntexaFoundationRuntime(
                    checkpoint_dir=checkpoint_dir or os.getenv("SYNTEXA_FOUNDATION_CHECKPOINT_DIR")
                )
    return _RUNTIME


def foundation_generate(messages: List[Dict[str, str]], **kwargs: Any) -> str:
    rt = get_foundation_runtime()
    if not rt.is_ready():
        if not rt.load():
            raise RuntimeError(
                "Foundation Model não disponível. Treine o modelo primeiro: "
                "python -m vereda_ai.syntexa_core.foundation_trainer_cli"
            )
    return rt.chat(messages, **kwargs)


def foundation_generate_stream(messages: List[Dict[str, str]], **kwargs: Any) -> Iterator[str]:
    rt = get_foundation_runtime()
    if not rt.is_ready():
        if not rt.load():
            raise RuntimeError(
                "Foundation Model não disponível. Treine o modelo primeiro."
            )
    yield from rt.chat_stream(messages, **kwargs)


def is_foundation_available() -> bool:
    try:
        rt = get_foundation_runtime()
        if rt.is_ready():
            return True
        return rt.load()
    except Exception:
        return False
