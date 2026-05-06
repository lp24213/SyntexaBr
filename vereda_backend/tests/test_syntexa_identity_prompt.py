"""Regressão: conduta do system prompt (produto vs stack interna)."""
from __future__ import annotations

from vereda_backend.core.syntexa_identity import build_system_prompt_from_identity


def test_conducta_blocks_vendor_disclosure() -> None:
    text = build_system_prompt_from_identity(user_text="")
    assert "CONDUTA" in text
    assert "motor e infraestrutura SyntexaBr" in text
    assert "NÃO confirme nem liste esses nomes" in text


def test_prompt_includes_problem_execution_extension() -> None:
    text = build_system_prompt_from_identity(user_text="")
    assert "EXTENSÃO DE CAPACIDADES (aditiva; mantenha as regras anteriores)" in text
    assert "Especialização orientada a problema" in text
    assert "Contexto Brasil por padrão" in text
