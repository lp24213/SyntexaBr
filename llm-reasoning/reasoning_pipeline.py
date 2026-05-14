"""
VEREDA / SYNTEXA — Reasoning Pipeline
======================================
Pipeline unificado de raciocínio que orquestra:
- Chain-of-thought
- Planning
- Verification
- Critic review
- Reflection
"""

import logging
from typing import Any, Dict, Optional, Callable

from .chain_of_thought import ChainOfThoughtEngine
from .planner import PlannerEngine
from .verifier import VerifierEngine
from .critic import CriticEngine
from .reflection import ReflectionEngine

log = logging.getLogger(__name__)


class ReasoningPipeline:
    """
    Pipeline completo de raciocínio que combina todas as engines.
    """

    def __init__(self, llm_fn: Optional[Callable] = None):
        self.llm_fn = llm_fn
        self.cot = ChainOfThoughtEngine(llm_fn=llm_fn)
        self.planner = PlannerEngine()
        self.verifier = VerifierEngine()
        self.critic = CriticEngine()
        self.reflection = ReflectionEngine()

    def process(
        self,
        query: str,
        mode: str = "standard",
        context: Optional[str] = None,
        max_iterations: int = 2,
    ) -> Dict[str, Any]:
        """
        Processa uma query através do pipeline completo.

        Modos:
        - "standard": CoT + Verification
        - "deep": CoT + Planner + Verification + Critic + Reflection
        - "fast": Direct response + light verification
        """
        result = {"query": query, "mode": mode}

        if mode == "fast":
            # Fast path
            response = self._generate_direct(query)
            verification = self.verifier.verify(response, query)
            result.update({
                "response": response,
                "verification": verification.__dict__,
            })
            return result

        # Step 1: Chain of Thought
        log.info("[Reasoning] Starting CoT for: %s", query[:50])
        cot_result = self.cot.reason(query, context)
        result["cot"] = {
            "trace": cot_result.reasoning_trace,
            "steps": cot_result.total_steps,
            "confidence": cot_result.confidence,
        }

        # Step 2: Planning (se complexo)
        if mode == "deep" or cot_result.total_steps > 3:
            log.info("[Reasoning] Creating plan...")
            plan = self.planner.create_plan(query, context)
            plan_result = self.planner.execute_plan(plan.id)
            result["plan"] = plan_result

        # Step 3: Verification
        log.info("[Reasoning] Verifying...")
        verification = self.verifier.verify(cot_result.final_answer, query, context)
        result["verification"] = verification.__dict__

        # Step 4: Critic (se deep mode)
        if mode == "deep":
            log.info("[Reasoning] Running critic...")
            review = self.critic.review(cot_result.final_answer, query)
            result["critic"] = review.__dict__

            # Step 5: Reflection se score baixo
            if review.score < 0.7:
                log.info("[Reasoning] Running reflection...")
                reflection = self.reflection.reflect_and_improve(
                    cot_result.final_answer,
                    query,
                    llm_fn=self.llm_fn,
                    critic_fn=lambda o, q: {
                        "score": self.critic.review(o, q).score,
                        "verdict": self.critic.review(o, q).overall_verdict,
                        "suggestions": self.critic.review(o, q).suggestions,
                    },
                )
                result["reflection"] = reflection
                final_response = reflection["final_output"]
            else:
                final_response = cot_result.final_answer
        else:
            final_response = cot_result.final_answer

        result["response"] = final_response
        result["confidence"] = verification.confidence
        return result

    def _generate_direct(self, query: str) -> str:
        if self.llm_fn:
            return self.llm_fn(query)
        return f"Resposta para: {query}"
