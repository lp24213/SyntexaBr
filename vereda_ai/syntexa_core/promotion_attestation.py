# -*- coding: utf-8 -*-
"""
Atestação de promoção LLM: agrega fingerprints do registry, bundle (manifest/assinatura)
e política de chat — padrão semelhante a artefactos versionados em stacks OSS (vLLM/K8s:
imagens digest, readiness, rollback auditável).
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from vereda_ai.syntexa_core.model_manifest import ModelManifest
from vereda_ai.syntexa_core.model_registry import _primary_registry_path, get_registry


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _manifest_paths(name: str) -> list[Path]:
    root = Path(".").resolve()
    return [
        root / "config" / f"{name}.manifest.json",
        root / "checkpoints" / name / "manifest.json",
    ]


def load_manifest_for_name(name: str) -> ModelManifest | None:
    for p in _manifest_paths(name):
        if p.is_file():
            try:
                return ModelManifest.from_file(p)
            except Exception:
                continue
    return None


def bundle_fingerprint_for_model(model_name: str) -> dict[str, Any]:
    """Fingerprint do bundle sem carregar pesos (manifest + assinatura + metadados do checkpoint)."""
    fp: dict[str, Any] = {
        "model_name": model_name,
        "manifest_path": None,
        "manifest_sha256": None,
        "bundle_signature_sha256": None,
        "tokenizer_path": None,
        "checkpoint_path": None,
        "checkpoint_bytes": None,
        "checkpoint_mtime_ns": None,
    }
    manifest = load_manifest_for_name(model_name)
    if not manifest:
        return fp
    fp["tokenizer_path"] = str(manifest.tokenizer_path)
    fp["checkpoint_path"] = str(manifest.checkpoint_path)
    ck = Path(manifest.checkpoint_path)
    if ck.is_file():
        try:
            st = ck.stat()
            fp["checkpoint_bytes"] = st.st_size
            fp["checkpoint_mtime_ns"] = st.st_mtime_ns
        except OSError:
            pass
    for p in _manifest_paths(model_name):
        if p.is_file():
            fp["manifest_path"] = str(p)
            fp["manifest_sha256"] = _sha256_file(p)
            sig = p.parent / "bundle.signature.json"
            if sig.is_file():
                fp["bundle_signature_sha256"] = _sha256_file(sig)
            break
    return fp


def registry_fingerprint() -> dict[str, Any]:
    p = _primary_registry_path()
    reg = get_registry()
    out: dict[str, Any] = {
        "registry_path": str(p),
        "registry_sha256": _sha256_file(p) if p.is_file() else None,
        "active": reg.active,
    }
    return out


def policy_fingerprint(policy_snapshot: dict[str, Any]) -> dict[str, str | None]:
    return {
        "policy_version": str(policy_snapshot.get("policy_version") or ""),
        "policy_sha256": str(policy_snapshot.get("policy_sha256") or ""),
        "policy_profile": str(policy_snapshot.get("policy_profile") or ""),
    }


def _canonical_dumps(obj: dict[str, Any]) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def compute_attestation_digest(payload: dict[str, Any]) -> str:
    return _sha256_bytes(_canonical_dumps(payload).encode("utf-8"))


def build_llm_promotion_attestation(
    *,
    promotion_type: str,
    previous_active: str | None,
    candidate_model: str,
    active_after: str,
    readiness_report: dict[str, Any],
    policy_snapshot: dict[str, Any],
    admin_user_id: int | None,
    extra: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], str]:
    """
    Monta o documento de atestação e o digest SHA-256 (cadastrável em audit trail).
    Inclui fingerprints de bundle para previous e candidate quando aplicável.
    """
    ts = datetime.now(timezone.utc).isoformat()
    reg_fp = registry_fingerprint()
    prev_bundle = (
        bundle_fingerprint_for_model(str(previous_active))
        if previous_active
        else None
    )
    cand_bundle = bundle_fingerprint_for_model(candidate_model)
    active_bundle = bundle_fingerprint_for_model(active_after)
    body: dict[str, Any] = {
        "v": 1,
        "promotion_type": promotion_type,
        "ts_utc": ts,
        "previous_active": previous_active,
        "candidate_model": candidate_model,
        "active_after": active_after,
        "readiness_ready": bool(readiness_report.get("ready", False)),
        "readiness_active_model": readiness_report.get("active_model"),
        "readiness_checks": readiness_report.get("checks"),
        "policy": policy_fingerprint(policy_snapshot),
        "registry": reg_fp,
        "bundle_previous": prev_bundle,
        "bundle_candidate": cand_bundle,
        "bundle_active_after": active_bundle,
        "admin_user_id": admin_user_id,
    }
    if extra:
        body["extra"] = extra
    digest = compute_attestation_digest(body)
    body["attestation_sha256"] = digest
    return body, digest


def verify_attestation_document(doc: dict[str, Any]) -> tuple[bool, str, str | None]:
    """
    Valida integridade do documento de atestação (recomputa SHA-256 sem o campo declarado).
    Retorna (válido, mensagem, digest_recomputado).
    """
    if not isinstance(doc, dict):
        return False, "documento inválido: não é um objecto", None
    declared = doc.get("attestation_sha256")
    if not declared or not isinstance(declared, str):
        return False, "attestation_sha256 ausente ou inválido", None
    body = {k: v for k, v in doc.items() if k != "attestation_sha256"}
    expected = compute_attestation_digest(body)
    if expected != declared:
        return (
            False,
            f"digest divergente: declarado={declared[:16]}... recomputado={expected[:16]}...",
            expected,
        )
    return True, "ok", expected


def compact_audit_record(full: dict[str, Any]) -> str:
    """Resumo curto para coluna audit_logs.detail (o digest cobre integridade do documento completo)."""
    return _canonical_dumps(
        {
            "attestation_sha256": full.get("attestation_sha256"),
            "promotion_type": full.get("promotion_type"),
            "previous": full.get("previous_active"),
            "candidate": full.get("candidate_model"),
            "active_after": full.get("active_after"),
            "ts_utc": full.get("ts_utc"),
            "policy_sha256": (full.get("policy") or {}).get("policy_sha256"),
            "registry_sha256": (full.get("registry") or {}).get("registry_sha256"),
        }
    )
