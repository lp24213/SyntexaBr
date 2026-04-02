from typing import Any

from vereda_ai.tools.math_solver import MathSolver
from vereda_ai.tools.code_executor import CodeExecutor
from vereda_ai.core.logging import get_logger


logger = get_logger(__name__)


class Executor:
    """
    Executa tarefas usando ferramentas registradas (math, código, visão, etc.).
    """

    def __init__(self) -> None:
        self.math = MathSolver()
        self.code = CodeExecutor()

    def execute_task(self, task: Any) -> Any:
        desc = task.description.lower()
        logger.info("Executando tarefa: %s", desc)

        if "cálculo" in desc or "equação" in desc or "math" in desc:
            return {"todo": "usar MathSolver com problema específico", "task": desc}

        if "gerar código" in desc or "api" in desc or "aplicação" in desc:
            return {"todo": "usar LLM/code_generation_engine", "task": desc}

        return {"info": "Tarefa ainda não mapeada para ferramenta", "task": desc}

