from typing import List, Tuple

from vereda_ai.ai.llm_engine import LLMEngine


class Planner:
    """
    Quebra uma requisição do usuário em um plano textual + passos.
    """

    def __init__(self, llm: LLMEngine):
        self.llm = llm

    def create_plan(self, request: str) -> Tuple[str, List[str]]:
        messages = [
            {
                "role": "system",
                "content": (
                    "Você é um planejador de tarefas sênior. "
                    "Decomponha o pedido em passos numerados, claros e objetivos."
                ),
            },
            {"role": "user", "content": request},
        ]
        plan_text = self.llm.chat(messages)
        steps: List[str] = []
        for line in plan_text.splitlines():
            line = line.strip()
            if not line:
                continue
            # Remove marcadores simples (1., 2), -, etc.
            for prefix in ["- ", "* ", "• "]:
                if line.startswith(prefix):
                    line = line[len(prefix) :]
            steps.append(line)
        return plan_text, steps

