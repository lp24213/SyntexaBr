from dataclasses import dataclass
import time
from typing import Any, Dict, List, Optional

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

    def handle_request(
        self,
        user_input: str,
        execution_context: Optional[Dict[str, Any]] = None,
    ) -> AgentResult:
        plan, steps = self.planner.create_plan(user_input)
        execution_context = dict(execution_context or {})
        is_admin = bool(execution_context.get("is_admin", False))
        requested_max_steps = int(execution_context.get("max_steps", 0) or 0)
        default_max_steps = 64 if is_admin else 12
        max_steps = requested_max_steps if requested_max_steps > 0 else default_max_steps
        bounded_steps = steps if is_admin else steps[:max_steps]

        task_ids = self.task_manager.create_tasks(
            bounded_steps,
            base_metadata={
                "user_id": execution_context.get("user_id", "agent-system"),
                "is_admin": is_admin,
                "subscription_plan": execution_context.get("subscription_plan", "free"),
                "history": execution_context.get("history", []),
                "knowledge_snippets": execution_context.get("knowledge_snippets", []),
                "memory_snippets": execution_context.get("memory_snippets", []),
                "image_data": execution_context.get("image_data"),
                "image_path": execution_context.get("image_path"),
                "max_tokens": execution_context.get("max_tokens"),
            },
        )
        shared_state: Dict[str, Any] = {
            "completed_steps": [],
            "tool_usage": [],
            "facts": [],
            "last_output": "",
            "confidence_history": [],
            "domain_failures": {},
            "tool_failures": {},
            "tool_runtime": {},
            "now_ts": time.time(),
        }
        outputs: list[Any] = []
        for tid in task_ids:
            task = self.task_manager.get_task(tid)
            task.metadata["previous_outputs"] = list(outputs)
            task.metadata["execution_state"] = dict(shared_state)
            out = self.executor.execute_task(task)
            outputs.append(out)
            self.task_manager.mark_done(tid, out)
            shared_state = self._evolve_shared_state(shared_state, task.description, out)
            shared_state["now_ts"] = time.time()
        return AgentResult(plan=plan, steps=bounded_steps, outputs=outputs)

    @staticmethod
    def _evolve_shared_state(
        state: Dict[str, Any],
        step_description: str,
        output: Any,
    ) -> Dict[str, Any]:
        next_state = dict(state or {})
        completed = list(next_state.get("completed_steps", []))
        completed.append(step_description)
        next_state["completed_steps"] = completed[-30:]

        if isinstance(output, dict):
            tool = output.get("tool_used")
            if tool:
                tools = list(next_state.get("tool_usage", []))
                tools.append(tool)
                next_state["tool_usage"] = tools[-40:]
            final_output = str(output.get("final_output", "")).strip()
            if final_output:
                facts = list(next_state.get("facts", []))
                facts.append(final_output[:500])
                next_state["facts"] = facts[-20:]
                next_state["last_output"] = final_output[:1200]
            confidence = output.get("confidence")
            if isinstance(confidence, dict):
                history = list(next_state.get("confidence_history", []))
                score = float(confidence.get("score", 0.0) or 0.0)
                history.append(max(0.0, min(1.0, score)))
                next_state["confidence_history"] = history[-60:]
            failed = not bool(output.get("ok", False))
            pcheck = output.get("programmatic_check")
            if isinstance(pcheck, dict) and str(pcheck.get("status") or "") == "failed":
                failed = True
            if failed:
                domain = str(output.get("domain") or "unknown")
                domain_failures = dict(next_state.get("domain_failures", {}))
                domain_failures[domain] = int(domain_failures.get(domain, 0) or 0) + 1
                next_state["domain_failures"] = domain_failures
                if tool:
                    tool_failures = dict(next_state.get("tool_failures", {}))
                    tool_failures[tool] = int(tool_failures.get(tool, 0) or 0) + 1
                    next_state["tool_failures"] = tool_failures
            # SLO/runtime health por ferramenta (latencia, falhas, quarentena).
            runtime = dict(next_state.get("tool_runtime", {}))
            for attempt in list(output.get("attempts", [])) if isinstance(output.get("attempts"), list) else []:
                if not isinstance(attempt, dict):
                    continue
                tname = str(attempt.get("tool") or "unknown")
                entry = dict(runtime.get(tname, {}))
                calls = int(entry.get("calls", 0) or 0) + 1
                failures = int(entry.get("failures", 0) or 0) + (0 if bool(attempt.get("ok", False)) else 1)
                avg_ms = float(entry.get("avg_duration_ms", 0.0) or 0.0)
                dur = float(attempt.get("duration_ms", 0.0) or 0.0)
                next_avg = ((avg_ms * (calls - 1)) + max(0.0, dur)) / max(1, calls)
                consec = int(entry.get("consecutive_failures", 0) or 0)
                consec = 0 if bool(attempt.get("ok", False)) else (consec + 1)
                quarantined_until = float(entry.get("quarantined_until", 0.0) or 0.0)
                now_ts = float(next_state.get("now_ts", time.time()) or time.time())
                if consec >= 3:
                    quarantined_until = max(quarantined_until, now_ts + 120.0)
                entry.update(
                    {
                        "calls": calls,
                        "failures": failures,
                        "avg_duration_ms": round(next_avg, 2),
                        "consecutive_failures": consec,
                        "quarantined_until": quarantined_until,
                    }
                )
                runtime[tname] = entry
            next_state["tool_runtime"] = runtime
        return next_state

