"""Regressão: /health público não expõe URL nem fornecedor LLM real."""
from __future__ import annotations

from unittest.mock import patch

import pytest

from vereda_backend.api.v1.endpoints.health import _mask_llm_for_public, health_check


@pytest.mark.parametrize(
    "raw,expected",
    [
        ({}, {}),
        ({"status": "up"}, {"status": "up"}),
        (
            {"status": "up", "checked": "https://secret.example/v1/models", "provider": "ollama"},
            {"status": "up", "provider": "syntexa"},
        ),
        (
            {"status": "up", "checked": "http://10.0.0.1:11434/v1/models", "provider": "OPENAI"},
            {"status": "up", "provider": "syntexa"},
        ),
        (
            {"status": "up", "provider": "syntexa", "checked": "https://x"},
            {"status": "up", "provider": "syntexa"},
        ),
        (
            {"status": "up", "engine": "syntexa_native", "note": "x"},
            {"status": "up", "engine": "syntexa_native", "note": "x"},
        ),
        (
            {"status": "degraded", "http": 502, "checked": "https://leak", "provider": "ollama"},
            {"status": "degraded", "http": 502, "provider": "syntexa"},
        ),
    ],
)
def test_mask_llm_for_public(raw: dict, expected: dict) -> None:
    assert _mask_llm_for_public(raw) == expected


def test_mask_preserves_empty_provider() -> None:
    assert _mask_llm_for_public({"status": "not_configured"}) == {"status": "not_configured"}


def test_health_check_applies_mask_to_llm_service() -> None:
    with (
        patch(
            "vereda_backend.api.v1.endpoints.health._service_database",
            return_value={"status": "up"},
        ),
        patch(
            "vereda_backend.api.v1.endpoints.health._service_redis",
            return_value={"status": "not_configured"},
        ),
        patch(
            "vereda_backend.api.v1.endpoints.health._service_llm",
            return_value={
                "status": "up",
                "checked": "https://gateway.internal/v1/models",
                "provider": "ollama",
            },
        ),
    ):
        payload = health_check()
    assert payload["status"] == "ok"
    assert payload["healthy"] is True
    llm = payload["services"]["llm"]
    assert llm == {"status": "up", "provider": "syntexa"}
    assert "checked" not in llm
