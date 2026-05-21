"""
SYNTEXA ADMIN ROOT SOVEREIGN CONTROL
======================================
Camada de controle absoluto do administrador root.

A governança protege a stack contra sabotagem,
MAS O ADMIN ROOT TEM AUTORIDADE TOTAL E IRRESTRITA.

Uso:
    from vereda_ai.syntexa_core.admin_control import (
        admin_session, root_override, require_admin,
        set_dev_mode, set_production_mode, is_admin_active,
    )

    @require_admin
    def update_architecture(new_config):
        # Admin pode modificar qualquer coisa
        ...
"""
from __future__ import annotations

import functools
import hashlib
import hmac
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Optional, Set

log = logging.getLogger(__name__)


# ── ENVIRONMENT VARIABLES ───────────────────────────────────
# O admin configura via environment; nunca hardcoded.

ENV_ROOT_EMAIL = "SYNTEXA_ROOT_ADMIN_EMAIL"
ENV_ROOT_KEY = "SYNTEXA_ROOT_ADMIN_KEY"
ENV_ROOT_TOKEN = "SYNTEXA_ROOT_OVERRIDE_TOKEN"
ENV_DEV_MODE = "SYNTEXA_DEV_MODE"
ENV_PROD_MODE = "SYNTEXA_PRODUCTION_MODE"


class RuntimeMode(Enum):
    """Modos de operação do runtime Syntexa."""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    MAINTENANCE = "maintenance"
    EXPERIMENTAL = "experimental"


@dataclass
class AdminSession:
    """
    Sessão de admin root autenticada.
    """
    email: str
    token_hash: str
    authenticated_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    permissions: Set[str] = field(default_factory=lambda: {"*"})  # * = todas
    audit_log: list[Dict[str, Any]] = field(default_factory=list)

    def is_valid(self) -> bool:
        if self.expires_at and time.time() > self.expires_at:
            return False
        return True

    def has_permission(self, action: str) -> bool:
        if "*" in self.permissions:
            return True
        return action in self.permissions

    def log_action(self, action: str, details: Optional[str] = None) -> None:
        entry = {
            "timestamp": time.time(),
            "action": action,
            "details": details,
        }
        self.audit_log.append(entry)
        log.info("[AdminSession] %s | %s", action, details or "")

    def revoke(self) -> None:
        self.expires_at = 0.0


class _AdminRuntime:
    """Singleton do runtime de controle admin."""

    def __init__(self):
        self._session: Optional[AdminSession] = None
        self._mode = RuntimeMode.DEVELOPMENT if os.getenv(ENV_DEV_MODE, "").lower() in ("true", "1", "yes") else (
            RuntimeMode.PRODUCTION if os.getenv(ENV_PROD_MODE, "").lower() in ("true", "1", "yes") else RuntimeMode.DEVELOPMENT
        )
        self._root_override_enabled = False
        self._bypass_guard = False

    @property
    def mode(self) -> RuntimeMode:
        return self._mode

    @property
    def session(self) -> Optional[AdminSession]:
        return self._session

    def is_admin_active(self) -> bool:
        return self._session is not None and self._session.is_valid()

    def is_root_override(self) -> bool:
        return self._root_override_enabled and self.is_admin_active()

    def can_bypass_guard(self) -> bool:
        return self._bypass_guard and self.is_admin_active()

    # ── AUTHENTICATION ────────────────────────────────────

    def authenticate(self, email: str, key: str, token: Optional[str] = None) -> Optional[AdminSession]:
        """
        Autentica admin root via email + key + token opcional.
        Comparativos são feitos com HMAC-SHA256 (timing-safe).
        """
        expected_email = os.getenv(ENV_ROOT_EMAIL, "")
        expected_key = os.getenv(ENV_ROOT_KEY, "")
        expected_token = os.getenv(ENV_ROOT_TOKEN, "")

        if not expected_email or not expected_key:
            log.warning("[AdminControl] Variáveis de admin não configuradas. Autenticação falhou.")
            return None

        # Timing-safe comparison
        email_ok = hmac.compare_digest(email.encode("utf-8"), expected_email.encode("utf-8"))
        key_ok = hmac.compare_digest(key.encode("utf-8"), expected_key.encode("utf-8"))

        token_ok = True
        if expected_token and token:
            token_ok = hmac.compare_digest(token.encode("utf-8"), expected_token.encode("utf-8"))

        if email_ok and key_ok and token_ok:
            token_hash = hashlib.sha256(f"{email}:{time.time()}".encode()).hexdigest()[:16]
            self._session = AdminSession(
                email=email,
                token_hash=token_hash,
                expires_at=time.time() + 3600 * 8,  # 8 horas
            )
            log.warning("[AdminControl] ROOT AUTHENTICATED: %s", email)
            return self._session

        log.warning("[AdminControl] Autenticação falhou para %s", email)
        return None

    def logout(self) -> None:
        if self._session:
            log.warning("[AdminControl] Admin %s desconectado.", self._session.email)
            self._session.revoke()
            self._session = None
        self._root_override_enabled = False
        self._bypass_guard = False

    # ── MODES ──────────────────────────────────────────────

    def set_mode(self, mode: RuntimeMode) -> None:
        if not self.is_admin_active():
            raise PermissionError("Apenas admin root pode alterar o modo de runtime.")
        old = self._mode
        self._mode = mode
        log.warning("[AdminControl] Modo alterado: %s -> %s", old.value, mode.value)
        if self._session:
            self._session.log_action("mode_change", f"{old.value} -> {mode.value}")

    def set_dev_mode(self) -> None:
        self.set_mode(RuntimeMode.DEVELOPMENT)

    def set_production_mode(self) -> None:
        self.set_mode(RuntimeMode.PRODUCTION)

    def set_maintenance_mode(self) -> None:
        self.set_mode(RuntimeMode.MAINTENANCE)

    def set_experimental_mode(self) -> None:
        self.set_mode(RuntimeMode.EXPERIMENTAL)

    # ── OVERRIDES ───────────────────────────────────────────

    def enable_root_override(self) -> None:
        if not self.is_admin_active():
            raise PermissionError("Apenas admin root pode ativar override.")
        self._root_override_enabled = True
        self._bypass_guard = True
        log.warning("[AdminControl] ROOT OVERRIDE ATIVADO")
        if self._session:
            self._session.log_action("root_override_enabled")

    def disable_root_override(self) -> None:
        self._root_override_enabled = False
        self._bypass_guard = False
        log.warning("[AdminControl] Root override desativado.")

    # ── INTERNAL ACCESS ───────────────────────────────────

    def get_runtime_state(self) -> Dict[str, Any]:
        """Retorna estado completo do runtime para debug do admin."""
        if not self.is_admin_active():
            raise PermissionError("Acesso negado. Admin não autenticado.")

        state = {
            "mode": self._mode.value,
            "root_override": self._root_override_enabled,
            "bypass_guard": self._bypass_guard,
            "admin_active": self.is_admin_active(),
            "session_valid": self._session.is_valid() if self._session else False,
            "session_email": self._session.email if self._session else None,
            "timestamp": time.time(),
        }

        # Coleta métricas de GPU se disponível
        try:
            import torch
            if torch.cuda.is_available():
                state["gpu"] = {
                    "name": torch.cuda.get_device_name(0),
                    "memory_allocated_mb": round(torch.cuda.memory_allocated() / (1024 ** 2), 1),
                    "memory_reserved_mb": round(torch.cuda.memory_reserved() / (1024 ** 2), 1),
                    "total_memory_mb": round(torch.cuda.get_device_properties(0).total_memory / (1024 ** 2), 1),
                }
        except Exception:
            pass

        return state

    def access_module(self, module_name: str) -> Any:
        """Admin acessa qualquer módulo interno diretamente."""
        if not self.is_admin_active():
            raise PermissionError("Acesso negado.")
        import importlib
        mod = importlib.import_module(module_name)
        self._session.log_action("module_access", module_name)
        return mod

    def get_model_weights_info(self) -> Dict[str, Any]:
        """Admin acessa informações dos pesos do modelo."""
        if not self.is_admin_active():
            raise PermissionError("Acesso negado.")
        from vereda_ai.syntexa_core.foundation_runtime import get_foundation_runtime
        rt = get_foundation_runtime()
        info = {
            "ready": rt.is_ready(),
            "device": rt.engine.device if rt.engine else None,
        }
        self._session.log_action("weights_access")
        return info


# ── SINGLETON ─────────────────────────────────────────────
_admin_runtime: Optional[_AdminRuntime] = None


def get_admin_runtime() -> _AdminRuntime:
    global _admin_runtime
    if _admin_runtime is None:
        _admin_runtime = _AdminRuntime()
    return _admin_runtime


# ── PUBLIC API ────────────────────────────────────────────

def authenticate_admin(email: str, key: str, token: Optional[str] = None) -> Optional[AdminSession]:
    return get_admin_runtime().authenticate(email, key, token)


def logout_admin() -> None:
    get_admin_runtime().logout()


def is_admin_active() -> bool:
    return get_admin_runtime().is_admin_active()


def is_root_override() -> bool:
    return get_admin_runtime().is_root_override()


def can_bypass_guard() -> bool:
    return get_admin_runtime().can_bypass_guard()


def set_dev_mode() -> None:
    get_admin_runtime().set_dev_mode()


def set_production_mode() -> None:
    get_admin_runtime().set_production_mode()


def set_maintenance_mode() -> None:
    get_admin_runtime().set_maintenance_mode()


def enable_root_override() -> None:
    get_admin_runtime().enable_root_override()


def disable_root_override() -> None:
    get_admin_runtime().disable_root_override()


def get_runtime_state() -> Dict[str, Any]:
    return get_admin_runtime().get_runtime_state()


# ── DECORATORS ─────────────────────────────────────────────

def require_admin(func: Callable) -> Callable:
    """Decorator: só executa se admin estiver autenticado."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not is_admin_active():
            raise PermissionError("Ação requer autenticação de admin root.")
        return func(*args, **kwargs)
    return wrapper


def root_override(func: Callable) -> Callable:
    """Decorator: função que requer root override ativo."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not is_root_override():
            raise PermissionError("Ação requer root override. Use enable_root_override().")
        return func(*args, **kwargs)
    return wrapper


def production_guard(func: Callable) -> Callable:
    """Decorator: em produção, requer admin ativo."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        rt = get_admin_runtime()
        if rt.mode == RuntimeMode.PRODUCTION and not is_admin_active():
            raise PermissionError("Em produção, esta ação requer autenticação admin.")
        return func(*args, **kwargs)
    return wrapper


def dev_or_admin(func: Callable) -> Callable:
    """Decorator: permite se dev mode OU admin ativo."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        rt = get_admin_runtime()
        if rt.mode not in (RuntimeMode.DEVELOPMENT, RuntimeMode.EXPERIMENTAL) and not is_admin_active():
            raise PermissionError("Ação permitida apenas em dev mode ou com admin.")
        return func(*args, **kwargs)
    return wrapper


# ── ADMIN CLI ─────────────────────────────────────────────

def _cli() -> None:
    import argparse
    ap = argparse.ArgumentParser(description="Syntexa Admin Root Control")
    ap.add_argument("--email", required=True)
    ap.add_argument("--key", required=True)
    ap.add_argument("--token", default=None)
    ap.add_argument("--action", choices=["auth", "state", "override", "mode"], default="auth")
    ap.add_argument("--mode-value", choices=["dev", "prod", "maint", "exp"], default=None)
    args = ap.parse_args()

    session = authenticate_admin(args.email, args.key, args.token)
    if not session:
        print("AUTH FAILED")
        sys.exit(1)

    if args.action == "auth":
        print(f"AUTH OK | {session.email} | {session.token_hash}")
    elif args.action == "state":
        import json
        print(json.dumps(get_runtime_state(), indent=2, default=str))
    elif args.action == "override":
        enable_root_override()
        print("ROOT OVERRIDE ENABLED")
    elif args.action == "mode":
        if args.mode_value == "dev":
            set_dev_mode()
        elif args.mode_value == "prod":
            set_production_mode()
        elif args.mode_value == "maint":
            set_maintenance_mode()
        elif args.mode_value == "exp":
            set_experimental_mode()
        print(f"MODE SET: {get_admin_runtime().mode.value}")


if __name__ == "__main__":
    _cli()
