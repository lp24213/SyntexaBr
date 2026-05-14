"""
VEREDA / SYNTEXA — Reflection Engine
=====================================
Engine de reflexão para auto-correção e melhoria iterativa.
"""

import time
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field

log = logging.getLogger(__name__)


@dataclass
class Reflection:
    iteration: int
    original_output: str
    critique: str
    improvements: List[str]
    revised_output: str
    confidence_delta: float
    timestamp: float = field(default_factory=time.time)


class ReflectionEngine:
    """
    Engine de reflexão que permite auto-correção iterativa.
    """

    def __init__(self, max_iterations: int = 3, min_confidence: float = 0.7):
        self.max_iterations = max_iterations
        self.min_confidence = min_confidence
        self._reflections: List[Reflection] = []

    def reflect_and_improve(
        self,
        original_output: str,
        query: str,
        llm_fn: Optional[Any] = None,
        critic_fn: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Pipeline de reflexão: gera → critica → melhora → repete.
        """
        current_output = original_output
        best_output = original_output
        best_confidence = 0.5

        for iteration in range(1, self.max_iterations + 1):
            # Critique current output
            critique = self._generate_critique(current_output, query, critic_fn)

            # Check if good enough
            if critique.get("score", 0) >= self.min_confidence:
                best_output = current_output
                best_confidence = critique["score"]
                break

            # Generate improvements
            improvements = critique.get("suggestions", [])

            # Revise output
            revised = self._revise_output(current_output, critique, query, llm_fn)

            reflection = Reflection(
                iteration=iteration,
                original_output=current_output,
                critique=critique.get("verdict", ""),
                improvements=improvements,
                revised_output=revised,
                confidence_delta=critique.get("score", 0) - best_confidence,
            )
            self._reflections.append(reflection)

            current_output = revised

            if critique.get("score", 0) > best_confidence:
                best_output = revised
                best_confidence = critique["score"]

            log.info("Reflection iteration %d: score=%.2f", iteration, critique.get("score", 0))

        return {
            "final_output": best_output,
            "iterations": len(self._reflections),
            "best_confidence": best_confidence,
            "reflection_history": [r.__dict__ for r in self._reflections],
        }

    def _generate_critique(self, output: str, query: str, critic_fn: Optional[Any]) -> Dict[str, Any]:
        if critic_fn:
            return critic_fn(output, query)
        # Fallback
        from .critic import CriticEngine
        critic = CriticEngine()
        review = critic.review(output, query)
        return {
            "score": review.score,
            "verdict": review.overall_verdict,
            "suggestions": review.suggestions,
            "strengths": review.strengths,
            "weaknesses": review.weaknesses,
        }

    def _revise_output(
        self,
        current: str,
        critique: Dict[str, Any],
        query: str,
        llm_fn: Optional[Any],
    ) -> str:
        if llm_fn:
            prompt = self._build_revision_prompt(current, critique, query)
            return llm_fn(prompt)

        # Fallback: apply simple fixes
        revised = current
        for suggestion in critique.get("suggestions", []):
            if "dividir" in suggestion.lower() or "shorter" in suggestion.lower():
                # Split long sentences
                revised = revised.replace(", ", ". ")
            if "adicionar dados" in suggestion.lower():
                revised += "\n\n[Nota: Dados específicos seriam inseridos aqui com acesso a fontes.]"
        return revised

    def _build_revision_prompt(self, current: str, critique: Dict[str, Any], query: str) -> str:
        parts = [
            "Revise o seguinte texto baseado na crítica fornecida.",
            "",
            "Texto original:",
            current,
            "",
            "Crítica:",
            f"Pontuação: {critique.get('score', 0)}",
            f"Veredito: {critique.get('verdict', '')}",
            "Sugestões:",
        ]
        for sugg in critique.get("suggestions", []):
            parts.append(f"- {sugg}")
        parts.extend(["", "Pergunta original:", query, "", "Texto revisado:"])
        return "\n".join(parts)

    def get_reflection_history(self) -> List[Reflection]:
        return self._reflections.copy()
