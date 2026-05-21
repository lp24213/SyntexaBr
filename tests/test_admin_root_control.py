"""
SYNTEXA ADMIN ROOT CONTROL TESTS
==================================
Testes de autoridade do admin root.
Verifica que:
1. Admin pode autenticar
2. Admin pode bypassar governança
3. Dev mode permite evolução
4. Produção protege sem admin
"""
from __future__ import annotations

import os
from unittest import mock

import pytest

from vereda_ai.syntexa_core.admin_control import (
    AdminSession,
    RuntimeMode,
    authenticate_admin,
    can_bypass_guard,
    disable_root_override,
    enable_root_override,
    get_admin_runtime,
    is_admin_active,
    is_root_override,
    logout_admin,
    require_admin,
    root_override,
    set_dev_mode,
    set_production_mode,
)


class TestAdminAuthentication:
    """Testa autenticação de admin."""

    def test_authenticate_with_correct_credentials(self):
        with mock.patch.dict(os.environ, {
            "SYNTEXA_ROOT_ADMIN_EMAIL": "root@syntexa.ai",
            "SYNTEXA_ROOT_ADMIN_KEY": "supersecretkey123",
        }):
            session = authenticate_admin("root@syntexa.ai", "supersecretkey123")
            assert session is not None
            assert session.email == "root@syntexa.ai"
            assert is_admin_active() is True
            logout_admin()

    def test_authenticate_with_wrong_credentials_fails(self):
        with mock.patch.dict(os.environ, {
            "SYNTEXA_ROOT_ADMIN_EMAIL": "root@syntexa.ai",
            "SYNTEXA_ROOT_ADMIN_KEY": "supersecretkey123",
        }):
            session = authenticate_admin("wrong@email.com", "wrongkey")
            assert session is None
            assert is_admin_active() is False

    def test_authenticate_requires_env_vars(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            session = authenticate_admin("root@syntexa.ai", "anykey")
            assert session is None


class TestRootOverride:
    """Testa root override e bypass de governança."""

    def test_enable_root_override_requires_admin(self):
        logout_admin()  # Garante que não há admin
        with pytest.raises(PermissionError):
            enable_root_override()

    def test_admin_can_enable_override(self):
        with mock.patch.dict(os.environ, {
            "SYNTEXA_ROOT_ADMIN_EMAIL": "root@syntexa.ai",
            "SYNTEXA_ROOT_ADMIN_KEY": "supersecretkey123",
        }):
            authenticate_admin("root@syntexa.ai", "supersecretkey123")
            enable_root_override()
            assert is_root_override() is True
            assert can_bypass_guard() is True
            disable_root_override()
            assert is_root_override() is False
            logout_admin()

    def test_logout_disables_override(self):
        with mock.patch.dict(os.environ, {
            "SYNTEXA_ROOT_ADMIN_EMAIL": "root@syntexa.ai",
            "SYNTEXA_ROOT_ADMIN_KEY": "supersecretkey123",
        }):
            authenticate_admin("root@syntexa.ai", "supersecretkey123")
            enable_root_override()
            assert is_root_override() is True
            logout_admin()
            assert is_admin_active() is False
            assert is_root_override() is False


class TestModeManagement:
    """Testa gestão de modos de runtime."""

    def test_set_dev_mode_requires_admin(self):
        logout_admin()
        with pytest.raises(PermissionError):
            set_dev_mode()

    def test_admin_can_switch_modes(self):
        with mock.patch.dict(os.environ, {
            "SYNTEXA_ROOT_ADMIN_EMAIL": "root@syntexa.ai",
            "SYNTEXA_ROOT_ADMIN_KEY": "supersecretkey123",
        }):
            authenticate_admin("root@syntexa.ai", "supersecretkey123")
            set_dev_mode()
            assert get_admin_runtime().mode == RuntimeMode.DEVELOPMENT
            set_production_mode()
            assert get_admin_runtime().mode == RuntimeMode.PRODUCTION
            logout_admin()


class TestDecorators:
    """Testa decorators de controle de acesso."""

    def test_require_admin_blocks_without_auth(self):
        logout_admin()

        @require_admin
        def secret_function():
            return "secret"

        with pytest.raises(PermissionError):
            secret_function()

    def test_require_admin_allows_with_auth(self):
        with mock.patch.dict(os.environ, {
            "SYNTEXA_ROOT_ADMIN_EMAIL": "root@syntexa.ai",
            "SYNTEXA_ROOT_ADMIN_KEY": "supersecretkey123",
        }):
            authenticate_admin("root@syntexa.ai", "supersecretkey123")

            @require_admin
            def secret_function():
                return "secret"

            assert secret_function() == "secret"
            logout_admin()

    def test_root_override_blocks_without_override(self):
        logout_admin()

        @root_override
        def override_function():
            return "overridden"

        with pytest.raises(PermissionError):
            override_function()


class TestDevMode:
    """Testa comportamento em dev mode."""

    def test_dev_mode_from_env(self):
        with mock.patch.dict(os.environ, {"SYNTEXA_DEV_MODE": "true"}):
            rt = get_admin_runtime()
            # Recria para ler env novo
            from vereda_ai.syntexa_core.admin_control import _AdminRuntime
            rt2 = _AdminRuntime()
            assert rt2.mode == RuntimeMode.DEVELOPMENT

    def test_production_mode_from_env(self):
        with mock.patch.dict(os.environ, {"SYNTEXA_PRODUCTION_MODE": "true"}):
            from vereda_ai.syntexa_core.admin_control import _AdminRuntime
            rt = _AdminRuntime()
            assert rt.mode == RuntimeMode.PRODUCTION


class TestAdminBypassesSovereignGuard:
    """Testa que admin root pode bypassar o SovereignGuard."""

    def test_guard_allows_bypass_when_admin_active(self):
        from vereda_ai.syntexa_core.sovereign_guard import SovereignGuard
        with mock.patch.dict(os.environ, {
            "SYNTEXA_ROOT_ADMIN_EMAIL": "root@syntexa.ai",
            "SYNTEXA_ROOT_ADMIN_KEY": "supersecretkey123",
        }):
            authenticate_admin("root@syntexa.ai", "supersecretkey123")
            enable_root_override()

            guard = SovereignGuard()
            ok, violations = guard.audit()
            assert ok is True, "Admin com override deve bypassar guard"
            assert len(violations) == 0

            disable_root_override()
            logout_admin()

    def test_guard_blocks_without_admin(self):
        from vereda_ai.syntexa_core.sovereign_guard import SovereignGuard
        logout_admin()

        guard = SovereignGuard()
        # Audit sem scan de arquivos (rápido)
        ok, violations = guard.audit(scan_python_files=False)
        # Pode passar se stack estiver OK, mas não deve bypassar
        assert guard._admin_can_bypass() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
