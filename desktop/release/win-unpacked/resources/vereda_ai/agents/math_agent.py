# -*- coding: utf-8 -*-
from typing import Any, Dict
from vereda_ai.agents.base_agent import BaseAgent
from vereda_ai.tools.math_tool import MathTool

class MathAgent(BaseAgent):
    name = "math"
    def __init__(self, llm=None):
        self.tool = MathTool()
        self.llm = llm
    def handle(self, prompt: str, context: Dict[str, Any]) -> str:
        prompt = (prompt or "").strip()
        lower = prompt.lower()
        expr = prompt
        for prefix in ("quanto e", "calcule", "calcular", "quanto da"):
            if lower.startswith(prefix):
                expr = prompt[len(prefix):].strip().rstrip("?.,;")
                break
        expr = expr.strip()
        if expr:
            out = self.tool.run(expression=expr)
            if out.get("ok"):
                return "Resultado: %s = %s." % (out["expression"], out["result"])
            if self.tool.available():
                return "Nao consegui avaliar: %s." % out.get("error", "erro")
        if self.llm:
            return self.llm.chat([{"role": "system", "content": "Especialista em matematica."}, {"role": "user", "content": prompt}])
        return "Envie uma expressao matematica para calcular."
