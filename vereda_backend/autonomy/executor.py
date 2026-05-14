"""
VEREDA / SYNTEXA — Autonomous Executor
=======================================
Executor autônomo com:
- Task creation
- Auto-prioritization
- Error detection
- Self-healing
- Recovery engine
"""

import uuid
import time
import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

log = logging.getLogger(__name__)


class TaskState(Enum):
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


@dataclass
class AutonomousTask:
    id: str
    name: str
    action: str
    payload: Dict[str, Any]
    state: TaskState = TaskState.CREATED
    priority: int = 5  # 1-10, menor = mais prioritário
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    retry_count: int = 0
    max_retries: int = 3
    result: Any = None
    error: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    worker_id: Optional[str] = None


class AutonomousExecutor:
    """
    Executor autônomo de tarefas com auto-recovery.
    """

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self._tasks: Dict[str, AutonomousTask] = {}
        self._queue: deque = deque()
        self._running: Dict[str, AutonomousTask] = {}
        self._handlers: Dict[str, Callable] = {}
        self._stats = {
            "tasks_created": 0,
            "tasks_completed": 0,
            "tasks_failed": 0,
            "retries": 0,
        }

    # ── TASK CREATION ────────────────────────────────────────
    def create_task(
        self,
        name: str,
        action: str,
        payload: Dict[str, Any],
        priority: int = 5,
        dependencies: Optional[List[str]] = None,
        max_retries: int = 3,
    ) -> str:
        """Cria nova tarefa autônoma."""
        task_id = str(uuid.uuid4())[:8]
        task = AutonomousTask(
            id=task_id,
            name=name,
            action=action,
            payload=payload,
            priority=priority,
            dependencies=dependencies or [],
            max_retries=max_retries,
        )
        self._tasks[task_id] = task
        self._queue.append(task)
        self._stats["tasks_created"] += 1

        # Auto-prioritize
        self._prioritize_queue()

        log.info("Task created: %s (%s) p=%d", task_id, name, priority)
        return task_id

    # ── AUTO-PRIORITIZATION ──────────────────────────────────
    def _prioritize_queue(self) -> None:
        """Reordena fila por prioridade e envelhecimento."""
        tasks = list(self._queue)
        now = time.time()

        def score(t):
            # Priority + aging bonus
            age_bonus = min(2, (now - t.created_at) / 60)  # max 2 points for waiting
            return t.priority - age_bonus

        tasks.sort(key=score)
        self._queue = deque(tasks)

    # ── EXECUTION ────────────────────────────────────────────
    def execute_next(self) -> Optional[AutonomousTask]:
        """Executa próxima tarefa da fila."""
        if not self._queue:
            return None
        if len(self._running) >= self.max_workers:
            return None

        # Find task with met dependencies
        ready_task = None
        for task in self._queue:
            if self._dependencies_met(task):
                ready_task = task
                break

        if not ready_task:
            return None

        self._queue.remove(ready_task)
        self._running[ready_task.id] = ready_task
        ready_task.state = TaskState.RUNNING
        ready_task.started_at = time.time()

        # Execute
        try:
            handler = self._handlers.get(ready_task.action)
            if handler:
                result = handler(ready_task.payload)
                ready_task.result = result
                ready_task.state = TaskState.COMPLETED
                self._stats["tasks_completed"] += 1
            else:
                ready_task.error = f"No handler for action: {ready_task.action}"
                ready_task.state = TaskState.FAILED
                self._stats["tasks_failed"] += 1

        except Exception as e:
            ready_task.error = str(e)
            ready_task.retry_count += 1

            if ready_task.retry_count < ready_task.max_retries:
                ready_task.state = TaskState.RETRYING
                self._stats["retries"] += 1
                # Re-queue with higher priority (lower number)
                ready_task.priority = max(1, ready_task.priority - 1)
                self._queue.appendleft(ready_task)
                log.warning("Task %s failed, retrying (%d/%d)", ready_task.id, ready_task.retry_count, ready_task.max_retries)
            else:
                ready_task.state = TaskState.FAILED
                self._stats["tasks_failed"] += 1
                log.error("Task %s failed after %d retries", ready_task.id, ready_task.retry_count)

        finally:
            ready_task.completed_at = time.time()
            if ready_task.id in self._running:
                del self._running[ready_task.id]

        return ready_task

    def _dependencies_met(self, task: AutonomousTask) -> bool:
        """Verifica se dependências da tarefa foram atendidas."""
        for dep_id in task.dependencies:
            dep_task = self._tasks.get(dep_id)
            if not dep_task or dep_task.state != TaskState.COMPLETED:
                return False
        return True

    # ── HANDLER REGISTRATION ─────────────────────────────────
    def register_handler(self, action: str, handler: Callable) -> None:
        self._handlers[action] = handler

    # ── MONITORING ───────────────────────────────────────────
    def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do executor."""
        return {
            "status": "healthy" if len(self._running) < self.max_workers else "busy",
            "queue_size": len(self._queue),
            "running": len(self._running),
            "total_tasks": len(self._tasks),
            **self._stats,
        }

    def get_task(self, task_id: str) -> Optional[AutonomousTask]:
        return self._tasks.get(task_id)

    def get_stats(self) -> Dict[str, Any]:
        return {
            **self._stats,
            "queue_size": len(self._queue),
            "running_count": len(self._running),
            "completion_rate": self._stats["tasks_completed"] / max(self._stats["tasks_created"], 1),
        }

    # ── SELF-HEALING ─────────────────────────────────────────
    def detect_and_heal(self) -> List[str]:
        """Detecta tarefas travadas e tenta recuperar."""
        healed = []
        now = time.time()
        timeout = 300  # 5 minutes

        for task_id, task in list(self._running.items()):
            if task.started_at and (now - task.started_at) > timeout:
                # Task stuck, force fail and retry
                task.state = TaskState.FAILED
                task.error = "Timeout - task stuck"
                del self._running[task_id]

                if task.retry_count < task.max_retries:
                    task.retry_count += 1
                    task.state = TaskState.RETRYING
                    task.priority = max(1, task.priority - 1)
                    self._queue.appendleft(task)
                    healed.append(task_id)
                    log.warning("Healed stuck task: %s", task_id)

        return healed
