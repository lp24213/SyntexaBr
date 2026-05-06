# -*- coding: utf-8 -*-
"""
Política de sistema do chat: versionada, com hash estável e perfis por ambiente.
O ficheiro JSON em disco pode ser substituído; o hash detecta drift.
"""
from __future__ import annotations

import copy
import hashlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[2]

_DEFAULT_POLICY: dict[str, Any] = {
    "version": "2026.04.30",
    "profiles": {
        "development": {
            "public": (
                "POLÍTICA DE ACESSO (PÚBLICO — DEV): respostas úteis; conformidade legal estrita; "
                "sem facilitar ilegalidade, abuso, fraude ou violação de privacidade. "
                "Ambiente de desenvolvimento: pode mencionar limitações de teste quando relevante."
            ),
            "authenticated": (
                "POLÍTICA DE ACESSO (USUÁRIO LOGADO — DEV): profundidade técnica; "
                "respeitar leis, LGPD e segurança operacional."
            ),
            "admin": (
                "POLÍTICA DE ACESSO (ADMIN — DEV): prioridade e profundidade máximas; "
                "automação e diagnósticos avançados. Conformidade legal: não instruir nem facilitar ato ilegal."
            ),
        },
        "staging": {
            "public": (
                "POLÍTICA DE ACESSO (PÚBLICO — STAGING): conformidade legal estrita; "
                "respostas úteis sem facilitar ilegalidade, abuso, fraude ou violação de privacidade."
            ),
            "authenticated": (
                "POLÍTICA DE ACESSO (USUÁRIO LOGADO — STAGING): profundidade técnica; "
                "leis, LGPD e segurança operacional."
            ),
            "admin": (
                "POLÍTICA DE ACESSO (ADMIN — STAGING): execução plena dos pedidos do administrador "
                "com profundidade técnica; manter conformidade legal (sem facilitar ato ilegal)."
            ),
        },
        "production": {
            "public": (
                "POLÍTICA DE ACESSO (PÚBLICO): resposta útil com conformidade legal estrita, "
                "sem facilitar ilegalidade, abuso, fraude ou violação de privacidade."
            ),
            "authenticated": (
                "POLÍTICA DE ACESSO (USUÁRIO LOGADO): responder com profundidade técnica, "
                "respeitando leis, LGPD e segurança operacional."
            ),
            "admin": (
                "POLÍTICA DE ACESSO (ADMIN): execute com prioridade máxima e profundidade total, "
                "incluindo automação, scripts e diagnósticos avançados. "
                "Não bloqueie por simplificações de UX. "
                "Mantenha conformidade legal: não instruir ou facilitar ato ilegal."
            ),
        },
    },
}


def _canonical_json_bytes(obj: dict[str, Any]) -> bytes:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _policy_path_from_settings() -> Path | None:
    try:
        from vereda_backend.core.config import settings

        raw = str(getattr(settings, "syntexa_chat_policy_path", "") or "").strip()
        if raw:
            p = Path(raw)
            p = p if p.is_absolute() else (_REPO_ROOT / p)
            if p.is_file():
                return p
    except Exception:
        pass
    default = _REPO_ROOT / "config" / "syntexa_chat_policy.json"
    return default if default.is_file() else None


def _load_policy_document() -> dict[str, Any]:
    path = _policy_path_from_settings()
    if path and path.is_file():
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    return copy.deepcopy(_DEFAULT_POLICY)


@lru_cache(maxsize=4)
def _cached_bundle(cache_key: str) -> dict[str, Any]:
    _ = cache_key  # invalidação por versão do processo; key inclui path mtime
    path = _policy_path_from_settings()
    doc = _load_policy_document()
    canonical = _canonical_json_bytes(doc)
    digest = _sha256_hex(canonical)
    version = str(doc.get("version") or "unknown")
    profiles = doc.get("profiles")
    if not isinstance(profiles, dict):
        profiles = _DEFAULT_POLICY["profiles"]
    return {
        "version": version,
        "sha256": digest,
        "profiles": profiles,
        "source": str(path) if path else "builtin",
    }


def policy_cache_key() -> str:
    path = _policy_path_from_settings()
    if path and path.is_file():
        try:
            return f"{path.resolve()}:{path.stat().st_mtime_ns}"
        except OSError:
            return str(path)
    return "builtin:v1"


def invalidate_policy_cache() -> None:
    _cached_bundle.cache_clear()


def resolve_policy_profile(environment: str, override: str | None = None) -> str:
    o = (override or "").strip().lower()
    if o in {"development", "staging", "production"}:
        return o
    env = (environment or "local").strip().lower()
    if env in {"prod", "production"}:
        return "production"
    if env in {"staging", "stage", "stg"}:
        return "staging"
    return "development"


def get_policy_snapshot() -> dict[str, Any]:
    """Metadados da política ativa (versão, hash, perfil efectivo, textos por tier)."""
    from vereda_backend.core.config import settings

    bundle = _cached_bundle(policy_cache_key())
    env = str(getattr(settings, "environment", "local") or "local")
    override = str(getattr(settings, "syntexa_chat_policy_profile", "") or "").strip() or None
    profile = resolve_policy_profile(env, override)
    profiles = bundle.get("profiles") or {}
    prof_obj = profiles.get(profile) or profiles.get("production")
    if not isinstance(prof_obj, dict):
        prof_obj = _DEFAULT_POLICY["profiles"]["production"]
    return {
        "policy_version": bundle["version"],
        "policy_sha256": bundle["sha256"],
        "policy_profile": profile,
        "environment": env,
        "profile_override": override,
        "source": bundle.get("source"),
        "tiers": {
            "public": prof_obj.get("public"),
            "authenticated": prof_obj.get("authenticated"),
            "admin": prof_obj.get("admin"),
        },
    }


def tier_prompt_block(access_tier: str) -> str:
    snap = get_policy_snapshot()
    tier = (access_tier or "public").strip().lower()
    tiers = snap.get("tiers") or {}
    text = tiers.get(tier) if isinstance(tiers, dict) else None
    if isinstance(text, str) and text.strip():
        return text.strip()
    # fallback embutido
    fallback = _DEFAULT_POLICY["profiles"]["production"]
    if tier == "admin":
        return str(fallback["admin"])
    if tier == "authenticated":
        return str(fallback["authenticated"])
    return str(fallback["public"])


def policy_trace_footer() -> str:
    snap = get_policy_snapshot()
    return (
        f"POLICY_REF version={snap['policy_version']} sha256={snap['policy_sha256'][:16]}... "
        f"profile={snap['policy_profile']}"
    )
