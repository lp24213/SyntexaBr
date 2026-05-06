"""Testes do LLMEngine (default = API real quando configurado, sem rede)."""
from __future__ import annotations

from types import SimpleNamespace

import pytest


def _settings_ollama_only() -> SimpleNamespace:
    return SimpleNamespace(
        ollama_endpoint="http://127.0.0.1:11434",
        ollama_model="llama3.2",
        ollama_api_key=None,
        local_llm_endpoint=None,
        openai_endpoint=None,
        openai_api_key=None,
        openai_model=None,
        exllama_endpoint=None,
        azure_tgi_endpoint=None,
        azure_openai_endpoint=None,
        azure_openai_key=None,
        azure_openai_deployment=None,
        remote_llm_endpoint=None,
        environment="development",
        default_llm="syntexa_native",
    )


def _settings_local_http_only() -> SimpleNamespace:
    return SimpleNamespace(
        ollama_endpoint=None,
        ollama_model=None,
        ollama_api_key=None,
        local_llm_endpoint="http://127.0.0.1:8080/v1",
        openai_endpoint=None,
        openai_api_key=None,
        openai_model=None,
        exllama_endpoint=None,
        azure_tgi_endpoint=None,
        azure_openai_endpoint=None,
        azure_openai_key=None,
        azure_openai_deployment=None,
        remote_llm_endpoint=None,
        environment="development",
        default_llm="syntexa_native",
    )


def _settings_native_only() -> SimpleNamespace:
    return SimpleNamespace(
        ollama_endpoint=None,
        ollama_model=None,
        ollama_api_key=None,
        local_llm_endpoint=None,
        openai_endpoint=None,
        openai_api_key=None,
        openai_model=None,
        exllama_endpoint=None,
        azure_tgi_endpoint=None,
        azure_openai_endpoint=None,
        azure_openai_key=None,
        azure_openai_deployment=None,
        remote_llm_endpoint=None,
        environment="development",
        default_llm="syntexa_native",
    )


def test_default_prefers_ollama_when_native_and_ollama_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("vereda_ai.ai.llm_engine.settings", _settings_ollama_only())
    from vereda_ai.ai.llm_engine import LLMEngine

    eng = LLMEngine()
    assert eng._default == "ollama"
    assert "ollama" in eng._providers


def test_default_prefers_local_http_when_native_and_endpoint_configured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("vereda_ai.ai.llm_engine.settings", _settings_local_http_only())
    from vereda_ai.ai.llm_engine import LLMEngine

    eng = LLMEngine()
    assert eng._default == "local_http"
    assert "local_http" in eng._providers


def test_default_stays_syntexa_native_when_no_external_chat_api(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("vereda_ai.ai.llm_engine.settings", _settings_native_only())
    from vereda_ai.ai.llm_engine import LLMEngine

    eng = LLMEngine()
    assert eng._default == "syntexa_native"
