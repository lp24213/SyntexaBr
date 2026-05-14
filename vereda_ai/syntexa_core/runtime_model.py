from __future__ import annotations

import threading
from pathlib import Path
from typing import Iterator, Optional

from vereda_ai.core.config import settings
from vereda_ai.core.logging import get_logger
from vereda_ai.syntexa_core.model_manifest import ModelManifest
from vereda_ai.syntexa_core.model_registry import get_registry
from vereda_ai.syntexa_core.tokenizer import SyntexaTokenizer
from vereda_ai.syntexa_core.neural_engine import is_neural_available

logger = get_logger(__name__)
_RUNTIME = None
_RUNTIME_NAME = None
_RUNTIME_LOCK = threading.Lock()


class _TorchRuntime:
    def __init__(self, manifest: ModelManifest):
        try:
            import torch  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("torch não disponível no runtime Syntexa.") from exc

        from training.model_syntexa import SyntexaConfig, SyntexaDecoderLM

        self.torch = torch
        self.manifest = manifest
        self.tokenizer = SyntexaTokenizer.load(manifest.tokenizer_path)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        payload = torch.load(manifest.checkpoint_path, map_location=self.device)
        cfg = SyntexaConfig(**(payload.get("config") or {}))
        self.model = SyntexaDecoderLM(cfg).to(self.device)
        self.model.load_state_dict(payload["model_state"], strict=True)
        self.model.eval()

    @staticmethod
    def _build_prompt(messages: list[dict[str, str]]) -> str:
        lines: list[str] = []
        for m in messages[-20:]:
            role = (m.get("role") or "user").upper()
            content = str(m.get("content") or "").strip()
            if not content:
                continue
            lines.append(f"{role}: {content}")
        lines.append("ASSISTANT:")
        return "\n".join(lines)

    def chat(self, messages: list[dict[str, str]]) -> str:
        prompt = self._build_prompt(messages)
        input_ids = self.tokenizer.encode(
            prompt,
            add_special_tokens=True,
            max_length=max(16, int(self.model.cfg.max_seq_len)),
        )
        with self.torch.no_grad():
            out_ids = self.model.generate(
                input_ids,
                max_new_tokens=max(32, int(getattr(settings, "own_model_max_new_tokens", 1024) or 1024)),
                temperature=float(getattr(settings, "own_model_temperature", 0.8) or 0.8),
                top_k=max(1, int(getattr(settings, "own_model_top_k", 80) or 80)),
                eos_id=self.tokenizer.eos_id,
                device=self.device,
            )
        comp = out_ids[len(input_ids) :]
        text = self.tokenizer.decode(comp).strip()
        if text:
            return text
        return "Syntexa model generated an empty reply."


def _manifest_candidates(name: str) -> list[Path]:
    root = Path(".").resolve()
    return [
        root / "config" / f"{name}.manifest.json",
        root / "checkpoints" / name / "manifest.json",
    ]


def _load_manifest(name: str) -> Optional[ModelManifest]:
    for p in _manifest_candidates(name):
        if p.is_file():
            try:
                return ModelManifest.from_file(p)
            except Exception as exc:
                logger.warning("Manifest inválido em %s: %s", p, exc)
    return None


def maybe_runtime_reply(messages: list[dict[str, str]]) -> Optional[str]:
    global _RUNTIME, _RUNTIME_NAME
    active = get_registry().get_active()
    if not active:
        return None
    if str(active.stage or "").lower() == "native_hybrid":
        return None
    with _RUNTIME_LOCK:
        if _RUNTIME is None or _RUNTIME_NAME != active.name:
            manifest = _load_manifest(active.name)
            if not manifest:
                return None
            try:
                _RUNTIME = _TorchRuntime(manifest)
                _RUNTIME_NAME = active.name
                logger.info("Syntexa own runtime (torch) inicializado para modelo ativo: %s", active.name)
            except Exception as exc:
                logger.warning("Não foi possível iniciar runtime Syntexa para '%s': %s", active.name, exc)
                _RUNTIME = None
                _RUNTIME_NAME = None
                return None
    try:
        return _RUNTIME.chat(messages) if _RUNTIME is not None else None
    except Exception as exc:
        logger.warning("Falha ao gerar resposta no runtime Syntexa: %s", exc)
        return None


def maybe_runtime_reply_stream(messages: list[dict[str, str]]) -> Optional[Iterator[str]]:
    text = maybe_runtime_reply(messages)
    if not text:
        return None
    chunk = max(16, min(256, int(getattr(settings, "own_model_top_k", 80) or 80)))

    def _iter() -> Iterator[str]:
        for i in range(0, len(text), chunk):
            yield text[i : i + chunk]

    return _iter()


def runtime_ready_for_active_model() -> tuple[bool, str]:
    active = get_registry().get_active()
    if not active:
        return False, "registry sem modelo ativo"
    if str(active.stage or "").lower() == "native_hybrid":
        return True, "modelo ativo é native_hybrid"
    # NeuralEngine (20B+ transformers) conta como runtime válido
    if is_neural_available():
        return True, "NeuralEngine disponível (transformers 20B+ 4-bit)"
    manifest = _load_manifest(active.name)
    if not manifest:
        return False, f"manifest não encontrado para '{active.name}'"
    try:
        _ = _TorchRuntime(manifest)
        return True, f"runtime torch OK para '{active.name}'"
    except Exception as exc:
        return False, f"falha ao inicializar runtime para '{active.name}': {exc}"


def runtime_readiness_report() -> dict[str, object]:
    active = get_registry().get_active()
    report: dict[str, object] = {
        "active_model": active.name if active else None,
        "active_stage": active.stage if active else None,
        "checks": [],
        "ready": False,
    }
    checks: list[dict[str, object]] = []
    report["checks"] = checks
    if not active:
        checks.append({"name": "registry_active", "ok": False, "detail": "registry sem modelo ativo"})
        return report
    checks.append({"name": "registry_active", "ok": True, "detail": f"modelo ativo: {active.name}"})
    if str(active.stage or "").lower() == "native_hybrid":
        checks.append({"name": "stage", "ok": True, "detail": "stage native_hybrid (sem checkpoint torch obrigatório)"})
        report["ready"] = True
        return report
    # NeuralEngine disponível?
    if is_neural_available():
        checks.append({"name": "neural_engine", "ok": True, "detail": "NeuralEngine disponível (transformers 20B+ 4-bit)"})
        report["ready"] = True
        return report
    checks.append({"name": "neural_engine", "ok": False, "detail": "NeuralEngine indisponível (torch/transformers não instalados)"})
    manifest = _load_manifest(active.name)
    if not manifest:
        checks.append({"name": "manifest", "ok": False, "detail": f"manifest não encontrado para '{active.name}'"})
        return report
    checks.append({"name": "manifest", "ok": True, "detail": str(manifest.checkpoint_path)})
    tok_ok = Path(manifest.tokenizer_path).is_file()
    checks.append({"name": "tokenizer_file", "ok": tok_ok, "detail": str(manifest.tokenizer_path)})
    ck_ok = Path(manifest.checkpoint_path).is_file()
    checks.append({"name": "checkpoint_file", "ok": ck_ok, "detail": str(manifest.checkpoint_path)})
    if not (tok_ok and ck_ok):
        return report
    try:
        _ = _TorchRuntime(manifest)
        checks.append({"name": "torch_runtime_init", "ok": True, "detail": f"runtime torch OK para '{active.name}'"})
        report["ready"] = True
        return report
    except Exception as exc:
        checks.append({"name": "torch_runtime_init", "ok": False, "detail": str(exc)})
        return report
