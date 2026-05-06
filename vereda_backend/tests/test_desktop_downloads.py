"""Downloads desktop: 302 para URL configurada ou página em_breve."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from vereda_backend.core.config import settings
from vereda_backend.main import app

client = TestClient(app)


def test_desktop_unknown_asset_404() -> None:
    r = client.get("/v1/desktop/assets/unknown.exe", follow_redirects=False)
    assert r.status_code == 404


def test_desktop_path_traversal_400() -> None:
    r = client.get("/v1/desktop/assets/%2e%2e%2fetc/passwd", follow_redirects=False)
    assert r.status_code == 400


def test_desktop_windows_fallback_when_url_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "desktop_windows_url", "")
    monkeypatch.setattr(settings, "api_public_base_url", "https://api.syntexabr.com.br")
    r = client.get("/v1/desktop/assets/SyntexaAI-Setup-1.0.0.exe", follow_redirects=False)
    assert r.status_code == 302
    loc = r.headers.get("location") or ""
    assert "/v1/desktop/binary/SyntexaAI-Setup-1.0.0.exe" in loc


def test_desktop_windows_redirect_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        settings,
        "desktop_windows_url",
        "https://releases.example/SyntexaAI-Setup-1.0.0.exe",
    )
    r = client.get("/v1/desktop/assets/SyntexaAI-Setup-1.0.0.exe", follow_redirects=False)
    assert r.status_code == 302
    assert r.headers.get("location") == "https://releases.example/SyntexaAI-Setup-1.0.0.exe"
