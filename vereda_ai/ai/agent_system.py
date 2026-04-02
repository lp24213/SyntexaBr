from dataclasses import dataclass
from typing import Any, List

from vereda_ai.agents.planner import Planner
from vereda_ai.agents.executor import Executor
from vereda_ai.agents.task_manager import TaskManager


@dataclass
class AgentResult:
    plan: str
    steps: List[str]
    outputs: List[Any]


class AgentSystem:
    """
    Pipeline completo de agentes:
    User Request -> Planner -> Task Decomposition -> Executor -> Validation (futuro)
    """

    def __init__(self, planner: Planner, executor: Executor, task_manager: TaskManager):
        self.planner = planner
        self.executor = executor
        self.task_manager = task_manager

    def handle_request(self, user_input: str) -> AgentResult:
        plan, steps = self.planner.create_plan(user_input)
        task_ids = self.task_manager.create_tasks(steps)
        outputs: list[Any] = []
        for tid in task_ids:
            task = self.task_manager.get_task(tid)
            out = self.executor.execute_task(task)
            outputs.append(out)
            self.task_manager.mark_done(tid, out)
        return AgentResult(plan=plan, steps=steps, outputs=outputs)

