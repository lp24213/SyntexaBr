# -*- coding: utf-8 -*-
from typing import Any, Dict
from vereda_ai.agents.base_agent import BaseAgent

class KnowledgeAgent(BaseAgent):
    name = "knowledge"
    def __init__(self, llm=None, rag=None):
        self.llm = llm
        self.rag = rag
    def handle(self, prompt: str, context: Dict[str, Any]) -> str:
        prompt = (prompt or "").strip()
        kb = context.get("knowledge_snippets") or []
        extra = ("\nContexto:\n" + "\n".join(kb[:5])) if kb else ""
        if self.llm:
            return self.llm.chat([
                {"role": "system", "content": "Assistente de conhecimento." + extra},
                {"role": "user", "content": prompt}
            ])
        return "Configure o LLM."
