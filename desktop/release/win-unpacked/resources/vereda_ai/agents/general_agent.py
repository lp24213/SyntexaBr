# -*- coding: utf-8 -*-
"""Agente geral: respostas amplas quando nenhum especialista se aplica."""
from typing import Any, Dict

from vereda_ai.agents.base_agent import BaseAgent


class GeneralAgent(BaseAgent):
    name = "general"

    def __init__(self, llm=None):
        self.llm = llm

    def handle(self, prompt: str, context: Dict[str, Any]) -> str:
        prompt = (prompt or "").strip()
        history = context.get("history") or []
        if self.llm:
            messages = [{"role": "system", "content": "Você é a Syntexa, assistente de IA brasileira. Responda de forma clara, objetiva e útil."}]
            for h in history[-6:]:
                messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
            messages.append({"role": "user", "content": prompt})
            return self.llm.chat(messages)
        return "Configure o LLM para respostas gerais."
