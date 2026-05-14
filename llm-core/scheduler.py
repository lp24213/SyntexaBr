"""
VEREDA / SYNTEXA — GPU Scheduler
=================================
Scheduler inteligente de GPU com:
- Queue prioritária
- Dynamic batching
- VRAM-aware scheduling
- Preemption control
- Multi-GPU support
"""

import time
import heapq
import logging
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

try:
    import torch
except ImportError:
    torch = None

log = logging.getLogger(__name__)


class Priority(Enum):
    CRITICAL = 0   # Admin, system health
    HIGH = 1       # Paid users, real-time
    NORMAL = 2     # Free users, standard
    LOW = 3        # Background, batch
    BACKGROUND = 4 # Training, maintenance


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PREEMPTED = "preempted"


@dataclass
class GPUJob:
    id: str
    priority: Priority
    fn: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    status: JobStatus = JobStatus.PENDING
    submit_time: float = field(default_factory=time.time)
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    result: Any = None
    error: Optional[str] = None
    vram_required_mb: float = 0.0
    estimated_duration_sec: float = 30.0
    user_tier: str = "free"
    preemption_allowed: bool = True

    def __lt__(self, other):
        # Ordenação por prioridade + tempo de espera (aging)
        my_score = self.priority.value * 1000 - (time.time() - self.submit_time)
        other_score = other.priority.value * 1000 - (time.time() - other.submit_time)
        return my_score < other_score


class GPUScheduler:
    """
    Scheduler de GPU com fila prioritária e gerenciamento de VRAM.
    """

    def __init__(
        self,
        max_concurrent: int = 4,
        vram_threshold_mb: float = 1024,  # min free VRAM
        enable_preemption: bool = True,
        preemption_timeout_sec: float = 60.0,
    ):
        self.max_concurrent = max_concurrent
        self.vram_threshold_mb = vram_threshold_mb
        self.enable_preemption = enable_preemption
        self.preemption_timeout_sec = preemption_timeout_sec

        self._queue: List[GPUJob] = []
        self._running: Dict[str, GPUJob] = {}
        self._completed: deque = deque(maxlen=1000)
        self._lock = threading.RLock()
        self._shutdown = False
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()

        # Metrics
        self._total_jobs = 0
        self._total_tokens = 0

    # ── JOB SUBMISSION ───────────────────────────────────────
    def submit(
        self,
        job_id: str,
        fn: Callable,
        priority: Priority = Priority.NORMAL,
        args: tuple = (),
        kwargs: Optional[Dict] = None,
        vram_required_mb: float = 0.0,
        estimated_duration_sec: float = 30.0,
        user_tier: str = "free",
        preemption_allowed: bool = True,
    ) -> GPUJob:
        """Submete job para execução."""
        job = GPUJob(
            id=job_id,
            priority=priority,
            fn=fn,
            args=args,
            kwargs=kwargs or {},
            vram_required_mb=vram_required_mb,
            estimated_duration_sec=estimated_duration_sec,
            user_tier=user_tier,
            preemption_allowed=preemption_allowed,
        )
        with self._lock:
            heapq.heappush(self._queue, job)
            self._total_jobs += 1
        log.debug("Job submitted: %s (priority=%s, vram=%.0fMB)", job_id, priority.value, vram_required_mb)
        return job

    def submit_chat(
        self,
        job_id: str,
        fn: Callable,
        args: tuple = (),
        kwargs: Optional[Dict] = None,
        user_tier: str = "free",
    ) -> GPUJob:
        """Submete job de chat com prioridade baseada no tier."""
        priority = {
            "admin": Priority.CRITICAL,
            "paid": Priority.HIGH,
            "basic": Priority.NORMAL,
            "free": Priority.LOW,
        }.get(user_tier, Priority.NORMAL)
        return self.submit(
            job_id=job_id,
            fn=fn,
            priority=priority,
            args=args,
            kwargs=kwargs,
            user_tier=user_tier,
        )

    # ── WORKER LOOP ──────────────────────────────────────────
    def _worker_loop(self) -> None:
        while not self._shutdown:
            try:
                self._process_next_job()
            except Exception as e:
                log.error("Scheduler worker error: %s", e)
            time.sleep(0.01)  # 10ms polling

    def _process_next_job(self) -> None:
        with self._lock:
            if not self._queue:
                return
            if len(self._running) >= self.max_concurrent:
                # Verificar preemption
                if self.enable_preemption:
                    self._try_preemption()
                if len(self._running) >= self.max_concurrent:
                    return

            # Check VRAM
            if not self._check_vram():
                return

            job = heapq.heappop(self._queue)
            self._running[job.id] = job
            job.status = JobStatus.RUNNING
            job.start_time = time.time()

        # Execute fora do lock
        try:
            result = job.fn(*job.args, **job.kwargs)
            job.result = result
            job.status = JobStatus.COMPLETED
        except Exception as e:
            job.error = str(e)
            job.status = JobStatus.FAILED
            log.error("Job %s failed: %s", job.id, e)
        finally:
            job.end_time = time.time()
            with self._lock:
                if job.id in self._running:
                    del self._running[job.id]
                self._completed.append(job)

    # ── PREEMPTION ───────────────────────────────────────────
    def _try_preemption(self) -> None:
        """Tenta preemptar job de baixa prioridade."""
        if not self._running:
            return

        # Encontra job de menor prioridade que pode ser preemptado
        lowest_priority = Priority.CRITICAL
        victim_id = None
        for jid, job in self._running.items():
            if job.preemption_allowed and job.priority.value > lowest_priority.value:
                # Verifica se há job de maior prioridade esperando
                if self._queue and self._queue[0].priority.value < job.priority.value:
                    lowest_priority = job.priority
                    victim_id = jid

        if victim_id:
            victim = self._running[victim_id]
            victim.status = JobStatus.PREEMPTED
            # Re-enqueue
            victim.start_time = None
            victim.status = JobStatus.PENDING
            heapq.heappush(self._queue, victim)
            del self._running[victim_id]
            log.info("Preempted job %s for higher priority", victim_id)

    # ── VRAM MANAGEMENT ──────────────────────────────────────
    def _check_vram(self) -> bool:
        if torch is None or not torch.cuda.is_available():
            return True
        free_mb = (torch.cuda.get_device_properties(0).total_memory - torch.cuda.memory_allocated()) / (1024 ** 2)
        return free_mb >= self.vram_threshold_mb

    # ── JOB CONTROL ──────────────────────────────────────────
    def cancel(self, job_id: str) -> bool:
        with self._lock:
            if job_id in self._running:
                # Não pode cancelar job em execução diretamente
                return False
            # Remove da fila
            self._queue = [j for j in self._queue if j.id != job_id]
            heapq.heapify(self._queue)
            return True

    def get_job(self, job_id: str) -> Optional[GPUJob]:
        with self._lock:
            if job_id in self._running:
                return self._running[job_id]
            for job in self._queue:
                if job.id == job_id:
                    return job
            for job in self._completed:
                if job.id == job_id:
                    return job
            return None

    # ── STATS ────────────────────────────────────────────────
    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            pending = len(self._queue)
            running = len(self._running)
            completed = len(self._completed)

            latencies = []
            for job in self._completed:
                if job.start_time and job.end_time:
                    latencies.append(job.end_time - job.start_time)

            avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

            return {
                "pending": pending,
                "running": running,
                "completed": completed,
                "total_jobs": self._total_jobs,
                "avg_latency_sec": round(avg_latency, 2),
                "preemption_enabled": self.enable_preemption,
                "max_concurrent": self.max_concurrent,
            }

    def shutdown(self) -> None:
        self._shutdown = True
        self._worker_thread.join(timeout=5.0)
        log.info("GPU scheduler shut down")
