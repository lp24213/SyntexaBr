"""
VEREDA / SYNTEXA — Planner Engine
==================================
Planejamento de tarefas com:
- Goal decomposition
- Task sequencing
- Dependency management
- Resource allocation
"""

import uuid
import logging
from typing import List, Dict, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum

log = logging.getLogger(__name__)


class TaskStatus(Enum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"


@dataclass
class Task:
    id: str
    description: str
    action: str
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = field(default_factory=list)
    outputs: Dict[str, Any] = field(default_factory=dict)
    retry_count: int = 0
    max_retries: int = 3
    estimated_duration_sec: float = 30.0
    priority: int = 0  # menor = mais prioritário
    assigned_worker: Optional[str] = None


@dataclass
class Plan:
    id: str
    goal: str
    tasks: List[Task]
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=lambda: __import__('time').time())
    completed_at: Optional[float] = None


class PlannerEngine:
    """
    Engine de planejamento que decompõe objetivos em tarefas executáveis.
    """

    def __init__(self):
        self._plans: Dict[str, Plan] = {}
        self._task_handlers: Dict[str, Any] = {}

    # ── PLAN CREATION ────────────────────────────────────────
    def create_plan(self, goal: str, context: Optional[str] = None) -> Plan:
        """
        Cria plano a partir de um objetivo.
        """
        tasks = self._decompose_goal(goal, context)
        plan = Plan(
            id=str(uuid.uuid4())[:8],
            goal=goal,
            tasks=tasks,
        )
        self._plans[plan.id] = plan
        self._update_task_statuses(plan)
        log.info("Plan created: %s (%d tasks)", plan.id, len(tasks))
        return plan

    def _decompose_goal(self, goal: str, context: Optional[str]) -> List[Task]:
        """Decompõe objetivo em tarefas."""
        # Heurística de decomposição baseada em keywords
        tasks = []
        goal_lower = goal.lower()

        if any(w in goal_lower for w in ["pesquisar", "research", "buscar", "find"]):
            tasks.append(Task(
                id="t1", description="Coletar fontes de informação",
                action="search", priority=0,
            ))
            tasks.append(Task(
                id="t2", description="Analisar e sintetizar resultados",
                action="analyze", dependencies=["t1"], priority=1,
            ))

        elif any(w in goal_lower for w in ["escrever", "write", "gerar", "generate", "criar", "create"]):
            tasks.append(Task(
                id="t1", description="Planejar estrutura",
                action="outline", priority=0,
            ))
            tasks.append(Task(
                id="t2", description="Gerar conteúdo",
                action="generate", dependencies=["t1"], priority=1,
            ))
            tasks.append(Task(
                id="t3", description="Revisar e refinar",
                action="review", dependencies=["t2"], priority=2,
            ))

        elif any(w in goal_lower for w in ["analisar", "analyze", "avaliar", "evaluate"]):
            tasks.append(Task(
                id="t1", description="Coletar dados",
                action="collect", priority=0,
            ))
            tasks.append(Task(
                id="t2", description="Processar e analisar",
                action="analyze", dependencies=["t1"], priority=1,
            ))
            tasks.append(Task(
                id="t3", description="Gerar relatório",
                action="report", dependencies=["t2"], priority=2,
            ))

        else:
            # Plano genérico
            tasks.append(Task(
                id="t1", description="Entender o problema",
                action="understand", priority=0,
            ))
            tasks.append(Task(
                id="t2", description="Executar ação principal",
                action="execute", dependencies=["t1"], priority=1,
            ))
            tasks.append(Task(
                id="t3", description="Verificar resultado",
                action="verify", dependencies=["t2"], priority=2,
            ))

        return tasks

    # ── PLAN EXECUTION ───────────────────────────────────────
    def execute_plan(self, plan_id: str) -> Dict[str, Any]:
        """
        Executa plano sequencialmente.
        """
        plan = self._plans.get(plan_id)
        if not plan:
            return {"error": "Plan not found"}

        plan.status = TaskStatus.RUNNING
        log.info("Executing plan: %s", plan_id)

        for task in plan.tasks:
            if task.status in (TaskStatus.COMPLETED, TaskStatus.SKIPPED):
                continue

            # Check dependencies
            if not self._dependencies_met(plan, task):
                task.status = TaskStatus.BLOCKED
                continue

            # Execute task
            task.status = TaskStatus.RUNNING
            try:
                result = self._execute_task(task)
                task.outputs = {"result": result}
                task.status = TaskStatus.COMPLETED
                log.info("Task %s completed", task.id)
            except Exception as e:
                task.retry_count += 1
                if task.retry_count >= task.max_retries:
                    task.status = TaskStatus.FAILED
                    log.error("Task %s failed after %d retries: %s", task.id, task.retry_count, e)
                else:
                    task.status = TaskStatus.PENDING
                    log.warning("Task %s failed, retrying (%d/%d)", task.id, task.retry_count, task.max_retries)

            self._update_task_statuses(plan)

        # Check overall status
        if all(t.status == TaskStatus.COMPLETED for t in plan.tasks):
            plan.status = TaskStatus.COMPLETED
            plan.completed_at = __import__('time').time()
        elif any(t.status == TaskStatus.FAILED for t in plan.tasks):
            plan.status = TaskStatus.FAILED

        return {
            "plan_id": plan_id,
            "status": plan.status.value,
            "tasks_completed": sum(1 for t in plan.tasks if t.status == TaskStatus.COMPLETED),
            "tasks_failed": sum(1 for t in plan.tasks if t.status == TaskStatus.FAILED),
            "total_tasks": len(plan.tasks),
        }

    def _dependencies_met(self, plan: Plan, task: Task) -> bool:
        for dep_id in task.dependencies:
            dep_task = next((t for t in plan.tasks if t.id == dep_id), None)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        return True

    def _execute_task(self, task: Task) -> Any:
        """Executa uma tarefa individual."""
        handler = self._task_handlers.get(task.action)
        if handler:
            return handler(task.description, task.outputs)
        # Default: retorna descrição como resultado
        return f"Executed: {task.description}"

    def _update_task_statuses(self, plan: Plan) -> None:
        """Atualiza status de tarefas baseado em dependências."""
        for task in plan.tasks:
            if task.status == TaskStatus.PENDING:
                if self._dependencies_met(plan, task):
                    task.status = TaskStatus.READY

    # ── TASK HANDLERS ────────────────────────────────────────
    def register_handler(self, action: str, handler: Any) -> None:
        self._task_handlers[action] = handler

    # ── PLAN QUERY ───────────────────────────────────────────
    def get_plan(self, plan_id: str) -> Optional[Plan]:
        return self._plans.get(plan_id)

    def get_ready_tasks(self, plan_id: str) -> List[Task]:
        plan = self._plans.get(plan_id)
        if not plan:
            return []
        return [t for t in plan.tasks if t.status == TaskStatus.READY]
