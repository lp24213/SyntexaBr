# -*- coding: utf-8 -*-
from typing import Any, Dict
from vereda_ai.agents.base_agent import BaseAgent

class CodeAgent(BaseAgent):
    name = "code"
    def __init__(self, llm=None):
        self.llm = llm
    def handle(self, prompt: str, context: Dict[str, Any]) -> str:
        prompt = (prompt or "").strip()
        if self.llm:
            return self.llm.chat([
                {"role": "system", "content": "Especialista em programacao. Explique e gere codigo quando pedido."},
                {"role": "user", "content": prompt}
            ])
        return "Solicite codigo ou explicacao."
