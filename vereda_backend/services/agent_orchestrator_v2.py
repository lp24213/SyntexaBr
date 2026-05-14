"""Syntexa Sovereign AI — Multi-Agent Orchestrator v2

Evolução do sistema de agentes com:
- Async communication
- Context exchange
- Task delegation
- Cooperative execution
- Retry logic
- Failure recovery
- Memory sharing

Integra-se ao AgentSystem existente sem quebrar APIs.
"""
from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    PLANNER = "planner"
    RESEARCHER = "researcher"
    CODER = "coder"
    SECURITY = "security"
    INFRASTRUCTURE = "infrastructure"
    QUANTUM = "quantum"
    MEMORY = "memory"
    VISION = "vision"
    AUDIO = "audio"
    REASONING = "reasoning"


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


@dataclass
class AgentTask:
    id: str
    role: AgentRole
    description: str
    context: Dict[str, Any] = field(default_factory=dict)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    retries: int = 0
    max_retries: int = 3
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    dependencies: List[str] = field(default_factory=list)
    subtasks: List["AgentTask"] = field(default_factory=list)


@dataclass
class AgentMessage:
    from_role: AgentRole
    to_role: AgentRole
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


class SharedMemory:
    """Memória compartilhada entre agentes."""
    
    def __init__(self):
        self._store: Dict[str, Any] = {}
        self._history: List[AgentMessage] = []
        self._lock = asyncio.Lock()
    
    async def set(self, key: str, value: Any) -> None:
        async with self._lock:
            self._store[key] = value
    
    async def get(self, key: str, default: Any = None) -> Any:
        async with self._lock:
            return self._store.get(key, default)
    
    async def append_message(self, msg: AgentMessage) -> None:
        async with self._lock:
            self._history.append(msg)
    
    async def get_history(self, role: Optional[AgentRole] = None) -> List[AgentMessage]:
        async with self._lock:
            if role is None:
                return list(self._history)
            return [m for m in self._history if m.to_role == role or m.from_role == role]
    
    def to_context_string(self) -> str:
        """Converte memória em string de contexto para prompts."""
        parts = []
        for k, v in self._store.items():
            parts.append(f"[{k}]: {v}")
        return "\n".join(parts)


class AsyncAgent:
    """Agente individual com execução async."""
    
    def __init__(self, role: AgentRole, llm_fn: Optional[Callable] = None):
        self.role = role
        self.llm_fn = llm_fn
        self.tasks_completed = 0
        self.tasks_failed = 0
    
    async def execute(self, task: AgentTask, memory: SharedMemory) -> str:
        """Executa tarefa e retorna resultado."""
        task.status = TaskStatus.RUNNING
        logger.info("[%s] Executing task: %s", self.role.value, task.description[:80])
        
        try:
            # Build prompt with shared memory context
            context = memory.to_context_string()
            prompt = self._build_prompt(task, context)
            
            # Execute via LLM or fallback
            if self.llm_fn:
                result = await self._call_llm(prompt)
            else:
                result = f"[{self.role.value}] Completed: {task.description}"
            
            task.result = result
            task.status = TaskStatus.COMPLETED
            task.completed_at = time.time()
            self.tasks_completed += 1
            
            # Share result with other agents
            await memory.set(f"result_{task.id}", result)
            await memory.append_message(AgentMessage(
                from_role=self.role,
                to_role=AgentRole.PLANNER,
                content=result,
                metadata={"task_id": task.id, "status": "completed"},
            ))
            
            return result
            
        except Exception as e:
            task.error = str(e)
            task.status = TaskStatus.FAILED
            self.tasks_failed += 1
            logger.error("[%s] Task failed: %s", self.role.value, e)
            raise
    
    def _build_prompt(self, task: AgentTask, context: str) -> str:
        return f"""You are a {self.role.value} agent.
Task: {task.description}
Context from other agents:
{context}
Provide a detailed, actionable response."""
    
    async def _call_llm(self, prompt: str) -> str:
        if asyncio.iscoroutinefunction(self.llm_fn):
            return await self.llm_fn(prompt)
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.llm_fn, prompt)


class MultiAgentOrchestratorV2:
    """Orquestrador multi-agente evoluído."""
    
    def __init__(self, llm_fn: Optional[Callable] = None):
        self.agents: Dict[AgentRole, AsyncAgent] = {}
        self.memory = SharedMemory()
        self.llm_fn = llm_fn
        self._task_counter = 0
    
    def register_agent(self, role: AgentRole) -> None:
        self.agents[role] = AsyncAgent(role, self.llm_fn)
        logger.info("Registered agent: %s", role.value)
    
    async def execute_plan(
        self,
        goal: str,
        required_agents: List[AgentRole],
        max_concurrent: int = 3,
    ) -> Dict[str, Any]:
        """Executa plano com múltiplos agentes cooperando."""
        
        # Phase 1: Planning
        planner = self.agents.get(AgentRole.PLANNER)
        if not planner:
            raise ValueError("Planner agent not registered")
        
        plan_task = self._create_task(AgentRole.PLANNER, f"Create plan for: {goal}")
        plan_result = await planner.execute(plan_task, self.memory)
        await self.memory.set("plan", plan_result)
        
        # Phase 2: Decompose into subtasks
        subtasks = self._decompose_plan(plan_result, required_agents)
        
        # Phase 3: Execute in dependency order with concurrency limit
        semaphore = asyncio.Semaphore(max_concurrent)
        results = {}
        
        async def run_task(task: AgentTask) -> None:
            async with semaphore:
                agent = self.agents.get(task.role)
                if not agent:
                    task.status = TaskStatus.FAILED
                    task.error = f"Agent {task.role.value} not available"
                    return
                
                # Wait for dependencies
                for dep_id in task.dependencies:
                    while True:
                        dep_task = next((t for t in subtasks if t.id == dep_id), None)
                        if dep_task and dep_task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED):
                            break
                        await asyncio.sleep(0.1)
                
                # Retry loop
                for attempt in range(task.max_retries + 1):
                    try:
                        result = await agent.execute(task, self.memory)
                        results[task.id] = result
                        break
                    except Exception:
                        task.retries += 1
                        if task.retries >= task.max_retries:
                            task.status = TaskStatus.FAILED
                            break
                        task.status = TaskStatus.RETRYING
                        await asyncio.sleep(0.5 * (2 ** attempt))
        
        await asyncio.gather(*[run_task(t) for t in subtasks])
        
        # Phase 4: Synthesize results
        return self._synthesize_results(goal, results, subtasks)
    
    def _create_task(self, role: AgentRole, description: str) -> AgentTask:
        self._task_counter += 1
        return AgentTask(
            id=f"task_{self._task_counter}",
            role=role,
            description=description,
        )
    
    def _decompose_plan(self, plan: str, roles: List[AgentRole]) -> List[AgentTask]:
        """Decompõe plano em subtasks (simplified heuristic)."""
        tasks = []
        for i, role in enumerate(roles):
            if role == AgentRole.PLANNER:
                continue
            task = self._create_task(
                role,
                f"Execute {role.value} task for plan: {plan[:200]}"
            )
            if i > 0:
                task.dependencies = [f"task_{i}"]
            tasks.append(task)
        return tasks
    
    def _synthesize_results(
        self,
        goal: str,
        results: Dict[str, str],
        tasks: List[AgentTask],
    ) -> Dict[str, Any]:
        """Sintetiza resultados dos agentes em resposta coesa."""
        successful = [t for t in tasks if t.status == TaskStatus.COMPLETED]
        failed = [t for t in tasks if t.status == TaskStatus.FAILED]
        
        return {
            "goal": goal,
            "plan": self.memory._store.get("plan", ""),
            "results": results,
            "agents_used": [t.role.value for t in successful],
            "completed_tasks": len(successful),
            "failed_tasks": len(failed),
            "success_rate": len(successful) / max(len(tasks), 1),
            "synthesis": "\n\n".join([
                f"[{t.role.value}]: {results.get(t.id, 'N/A')}"
                for t in successful
            ]),
            "shared_memory": self.memory.to_context_string(),
        }
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "agents": {role.value: {"completed": a.tasks_completed, "failed": a.tasks_failed}
                      for role, a in self.agents.items()},
            "memory_keys": len(self.memory._store),
            "message_history": len(self.memory._history),
        }


# Singleton para integração com backend existente
_orchestrator_v2: Optional[MultiAgentOrchestratorV2] = None


def get_orchestrator_v2(llm_fn: Optional[Callable] = None) -> MultiAgentOrchestratorV2:
    global _orchestrator_v2
    if _orchestrator_v2 is None:
        _orchestrator_v2 = MultiAgentOrchestratorV2(llm_fn)
        # Register default agents
        for role in [AgentRole.PLANNER, AgentRole.CODER, AgentRole.RESEARCHER,
                     AgentRole.SECURITY, AgentRole.INFRASTRUCTURE, AgentRole.QUANTUM]:
            _orchestrator_v2.register_agent(role)
    return _orchestrator_v2
