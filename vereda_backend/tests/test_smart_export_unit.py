"""Testes de smart_export: primário, corpo LLM e ramos financeiro/contrato (sem rede)."""
from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from vereda_backend.multimodal.smart_export import (
    _ensure_assistant_body,
    _export_primary,
    run_smart_export,
)


def test_export_primary_prefers_assistant_on_short_export_command() -> None:
    u = "Gere o pdf do que falámos"
    a = "Resposta longa do assistente com detalhes sobre o projeto e próximos passos."
    primary, merged = _export_primary(u, a)
    assert primary == a
    assert "Resposta longa" in merged


def test_export_primary_uses_user_when_no_assistant() -> None:
    u = "Só o pedido do utilizador sem resposta anterior."
    primary, merged = _export_primary(u, None)
    assert primary == u
    assert merged == u


def test_export_primary_prefers_user_spec_over_prior_assistant_bio() -> None:
    u = (
        "QUERO UMA PLANILHA DE ALIMENTAÇÃO SAUDÁVEL E CRESCIMENTO DE MASSA MUSCULAR EM ATÉ 6 MESES. "
        "NÃO QUERO BIOGRAFIA."
    )
    a = "Virginia Fonseca — DJ e influenciadora com milhões de seguidores."
    primary, merged = _export_primary(u, a)
    assert primary == u
    assert "Virginia" not in primary
    assert "Virginia" in merged


def test_ensure_assistant_body_returns_long_assistant_without_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_llm = MagicMock()
    import vereda_backend.ai_runtime as air

    monkeypatch.setattr(air, "llm_engine", mock_llm)
    long_a = "Z" * 250
    out = _ensure_assistant_body("qualquer pedido", long_a)
    assert out == long_a
    mock_llm.chat.assert_not_called()


def test_ensure_assistant_body_calls_llm_when_assistant_short(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_llm = MagicMock()
    mock_llm.chat.return_value = "Conteúdo sintético " * 10  # > 100 chars
    import vereda_backend.ai_runtime as air

    monkeypatch.setattr(air, "llm_engine", mock_llm)
    user = "Elabore um relatório detalhado de vendas trimestrais com tabelas " * 3
    out = _ensure_assistant_body(user, "curto")
    mock_llm.chat.assert_called_once()
    assert len(out) > 100


def test_run_smart_export_financial_uses_generic_table_when_primary_long() -> None:
    long_body = "Linha de dados " * 40  # >= 400 chars
    r = run_smart_export(
        "Gere uma planilha do meu orçamento financeiro com receitas e despesas",
        assistant_reply=long_body,
        generate_audio=False,
    )
    assert r["ok"] is True
    assert r["intent"] == "financial"
    assert "resposta do assistente" in r["summary"].lower()


def test_run_smart_export_contract_uses_conversation_pdf_when_primary_long() -> None:
    long_body = "Cláusula simulada " * 12  # >= 160 chars
    r = run_smart_export(
        "Gere um contrato de prestação de serviços",
        assistant_reply=long_body,
        generate_audio=False,
    )
    assert r["ok"] is True
    assert r["intent"] == "document"
    assert "texto da conversa" in r["summary"].lower()


def test_run_smart_export_ods_financial_long_primary_generic_table() -> None:
    long_body = "Dado " * 100  # >= 400
    r = run_smart_export(
        "Exporta em ODS o meu orçamento financeiro mensal",
        assistant_reply=long_body,
        generate_audio=False,
    )
    assert r["ok"] is True
    assert r["intent"] == "ods"
    assert "open" in r["summary"].lower() or "ods" in r["summary"].lower()
