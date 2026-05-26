"""
SYNTEXA QUANTUM SCHEDULER
===========================
Agendador híbrido clássico-quântico usando QPanda3.
Orquestra tarefas entre runtime neural (GPU) e runtime quântico (QPanda).
"""
from __future__ import annotations

import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable

log = logging.getLogger(__name__)

try:
    from pyqpanda import CPUQVM, QProg, H, RX, RY, RZ, CNOT, Measure, qvm
    QPANDA_AVAILABLE = True
except ImportError:
    QPANDA_AVAILABLE = False
    log.warning("pyqpanda não disponível — quantum scheduler usará simulação clássica")


class TaskType(Enum):
    CLASSICAL = "classical"
    QUANTUM = "quantum"
    HYBRID = "hybrid"


class TaskPriority(Enum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3


@dataclass
class QuantumTask:
    id: str
    task_type: TaskType
    priority: TaskPriority = TaskPriority.NORMAL
    payload: Dict[str, Any] = field(default_factory=dict)
    result: Optional[Any] = None
    status: str = "pending"  # pending, running, completed, failed
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    error: Optional[str] = None


class QuantumScheduler:
    """
    Agendador híbrido que distribui tarefas entre runtime clássico (GPU/PyTorch)
    e runtime quântico (QPanda3 CPUQVM).
    """

    def __init__(self, max_workers: int = 4, use_quantum: bool = True):
        self.max_workers = max_workers
        self.use_quantum = use_quantum and QPANDA_AVAILABLE
        self._tasks: Dict[str, QuantumTask] = {}
        self._queue: List[QuantumTask] = []
        self._lock = threading.RLock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._vm: Optional[Any] = None

        if self.use_quantum:
            self._init_qpanda()

        self._running = True
        self._scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._scheduler_thread.start()

    def _init_qpanda(self) -> None:
        try:
            self._vm = CPUQVM()
            self._vm.init_qvm()
            log.info("[QuantumScheduler] QPanda CPUQVM inicializado")
        except Exception as e:
            log.error("[QuantumScheduler] Falha ao inicializar QPanda: %s", e)
            self.use_quantum = False

    def submit(
        self,
        task_type: TaskType,
        payload: Dict[str, Any],
        priority: TaskPriority = TaskPriority.NORMAL,
        task_id: Optional[str] = None,
    ) -> str:
        """Submete tarefa para execução híbrida."""
        import uuid
        tid = task_id or str(uuid.uuid4())[:12]
        task = QuantumTask(
            id=tid,
            task_type=task_type,
            priority=priority,
            payload=payload,
        )
        with self._lock:
            self._tasks[tid] = task
            self._queue.append(task)
            self._queue.sort(key=lambda t: (t.priority.value, t.created_at))
        log.info("[QuantumScheduler] Tarefa %s submetida (type=%s, prio=%s)", tid, task_type.value, priority.name)
        return tid

    def _scheduler_loop(self) -> None:
        while self._running:
            task = None
            with self._lock:
                if self._queue:
                    task = self._queue.pop(0)
            if task:
                self._executor.submit(self._execute_task, task)
            else:
                time.sleep(0.01)

    def _execute_task(self, task: QuantumTask) -> None:
        task.status = "running"
        task.started_at = time.time()
        try:
            if task.task_type == TaskType.QUANTUM:
                task.result = self._run_quantum(task.payload)
            elif task.task_type == TaskType.HYBRID:
                task.result = self._run_hybrid(task.payload)
            else:
                task.result = self._run_classical(task.payload)
            task.status = "completed"
        except Exception as e:
            task.status = "failed"
            task.error = str(e)
            log.error("[QuantumScheduler] Tarefa %s falhou: %s", task.id, e)
        task.completed_at = time.time()

    def _run_classical(self, payload: Dict[str, Any]) -> Any:
        """Executa tarefa clássica (delega para função registrada)."""
        fn = payload.get("function")
        args = payload.get("args", [])
        kwargs = payload.get("kwargs", {})
        if callable(fn):
            return fn(*args, **kwargs)
        return {"error": "No callable function provided", "payload": payload}

    def _run_quantum(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Executa circuito quântico via QPanda3."""
        if not self.use_quantum or self._vm is None:
            return self._simulate_quantum_classical(payload)

        qubits_count = payload.get("qubits", 4)
        gates = payload.get("gates", [])
        shots = payload.get("shots", 1024)

        q = self._vm.qAlloc_many(qubits_count)
        c = self._vm.cAlloc_many(qubits_count)
        prog = QProg()

        for gate in gates:
            gtype = gate.get("gate")
            target = gate.get("target", 0)
            param = gate.get("param", 0.0)
            control = gate.get("control", 0)

            if gtype == "H":
                prog.insert(H(q[target]))
            elif gtype == "RX":
                prog.insert(RX(q[target], param))
            elif gtype == "RY":
                prog.insert(RY(q[target], param))
            elif gtype == "RZ":
                prog.insert(RZ(q[target], param))
            elif gtype == "CNOT":
                prog.insert(CNOT(q[control], q[target]))

        for i in range(qubits_count):
            prog.insert(Measure(q[i], c[i]))

        result = self._vm.run_with_configuration(prog, c, shots)

        return {
            "backend": "qpanda3",
            "qubits": qubits_count,
            "shots": shots,
            "outcomes": dict(result),
            "most_likely": max(result, key=result.get) if result else None,
        }

    def _simulate_quantum_classical(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Simulação clássica quando QPanda não está disponível."""
        import random
        qubits = payload.get("qubits", 4)
        shots = payload.get("shots", 1024)
        outcomes = {}
        for _ in range(shots):
            outcome = "".join(str(random.randint(0, 1)) for _ in range(qubits))
            outcomes[outcome] = outcomes.get(outcome, 0) + 1
        for k in outcomes:
            outcomes[k] = outcomes[k] / shots
        return {
            "backend": "classical_simulator",
            "qubits": qubits,
            "shots": shots,
            "outcomes": outcomes,
            "most_likely": max(outcomes, key=outcomes.get) if outcomes else None,
        }

    def _run_hybrid(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Executa pipeline híbrido: pré-processamento clássico + circuito quântico + pós-processamento."""
        classical_pre = payload.get("classical_pre", {})
        quantum = payload.get("quantum", {})
        classical_post = payload.get("classical_post", {})

        # Pré-processamento clássico
        pre_result = self._run_classical(classical_pre) if classical_pre else {}

        # Ajusta parâmetros do circuito com base no pré-processamento
        if "adjusted_params" in pre_result:
            quantum["gates"] = pre_result["adjusted_params"]

        # Execução quântica
        q_result = self._run_quantum(quantum)

        # Pós-processamento clássico
        post_payload = classical_post.copy()
        post_payload["quantum_result"] = q_result
        post_result = self._run_classical(post_payload) if classical_post else {}

        return {
            "hybrid": True,
            "classical_pre": pre_result,
            "quantum": q_result,
            "classical_post": post_result,
        }

    def get_result(self, task_id: str, timeout: Optional[float] = None) -> Optional[QuantumTask]:
        """Aguarda e retorna resultado da tarefa."""
        t0 = time.time()
        while True:
            with self._lock:
                task = self._tasks.get(task_id)
                if task and task.status in ("completed", "failed"):
                    return task
            if timeout and (time.time() - t0) > timeout:
                return None
            time.sleep(0.01)

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total = len(self._tasks)
            completed = sum(1 for t in self._tasks.values() if t.status == "completed")
            failed = sum(1 for t in self._tasks.values() if t.status == "failed")
            pending = sum(1 for t in self._tasks.values() if t.status == "pending")
            running = sum(1 for t in self._tasks.values() if t.status == "running")
        return {
            "total": total,
            "completed": completed,
            "failed": failed,
            "pending": pending,
            "running": running,
            "qpanda_available": QPANDA_AVAILABLE,
            "use_quantum": self.use_quantum,
        }

    def shutdown(self) -> None:
        self._running = False
        self._executor.shutdown(wait=True)
        if self._vm and QPANDA_AVAILABLE:
            self._vm.finalize()
        log.info("[QuantumScheduler] Shutdown completo")
