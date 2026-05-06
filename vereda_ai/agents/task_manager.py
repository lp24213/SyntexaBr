from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Task:
    id: str
    description: str
    status: str = "pending"
    result: Any = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskManager:
    """
    Gerencia o ciclo de vida de tarefas planejadas.
    """

    def __init__(self) -> None:
        self._tasks: Dict[str, Task] = {}

    def create_tasks(
        self,
        descriptions: List[str],
        base_metadata: Dict[str, Any] | None = None,
    ) -> List[str]:
        ids: List[str] = []
        shared = dict(base_metadata or {})
        for i, desc in enumerate(descriptions):
            tid = f"task-{i}"
            metadata = dict(shared)
            metadata["step_index"] = i
            metadata["total_steps"] = len(descriptions)
            self._tasks[tid] = Task(id=tid, description=desc, metadata=metadata)
            ids.append(tid)
        return ids

    def get_task(self, task_id: str) -> Task:
        return self._tasks[task_id]

    def mark_done(self, task_id: str, result: Any) -> None:
        task = self._tasks[task_id]
        task.status = "done"
        task.result = result

