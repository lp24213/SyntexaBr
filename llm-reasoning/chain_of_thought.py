"""
VEREDA / SYNTEXA — Chain of Thought Engine
===========================================
Implementa raciocínio passo a passo com:
- Decomposition
- Step-by-step generation
- Intermediate verification
- Backtracking
"""

import re
import logging
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field

log = logging.getLogger(__name__)


@dataclass
class ReasoningStep:
    number: int
    thought: str
    action: Optional[str] = None
    observation: Optional[str] = None
    is_verified: bool = False
    confidence: float = 0.0


@dataclass
class CoTResult:
    steps: List[ReasoningStep]
    final_answer: str
    total_steps: int
    backtracks: int = 0
    confidence: float = 0.0
    reasoning_trace: str = ""


class ChainOfThoughtEngine:
    """
    Engine de Chain-of-Thought para raciocínio estruturado.
    """

    def __init__(self, llm_fn: Optional[Callable] = None):
        self.llm_fn = llm_fn
        self.max_steps = 10
        self.min_confidence = 0.6

    # ── CORE CoT ─────────────────────────────────────────────
    def reason(
        self,
        question: str,
        context: Optional[str] = None,
        max_steps: int = 10,
    ) -> CoTResult:
        """
        Executa raciocínio passo a passo.
        """
        steps = []
        backtracks = 0
        current_thought = ""

        for step_num in range(1, max_steps + 1):
            # Generate next thought
            prompt = self._build_step_prompt(question, steps, step_num)
            thought_text = self._generate(prompt)

            # Parse step
            step = self._parse_step(step_num, thought_text)
            steps.append(step)

            # Verify step
            step.is_verified = self._verify_step(step, question, steps)
            step.confidence = self._score_confidence(step)

            # Check if done
            if self._is_final_answer(step, step_num, max_steps):
                break

            # Backtrack if low confidence
            if step.confidence < self.min_confidence and step_num > 1:
                steps.pop()
                backtracks += 1
                # Retry with modified prompt
                continue

        # Generate final answer
        final_answer = self._generate_final_answer(question, steps)
        trace = self._build_trace(steps)

        # Calculate overall confidence
        avg_confidence = sum(s.confidence for s in steps) / max(len(steps), 1)

        return CoTResult(
            steps=steps,
            final_answer=final_answer,
            total_steps=len(steps),
            backtracks=backtracks,
            confidence=avg_confidence,
            reasoning_trace=trace,
        )

    # ── PROMPT BUILDING ──────────────────────────────────────
    def _build_step_prompt(
        self,
        question: str,
        steps: List[ReasoningStep],
        step_num: int,
    ) -> str:
        parts = [
            "Pergunta: " + question,
            "",
            "Pense passo a passo. No formato:",
            "Passo N: [seu raciocínio]",
            "Ação: [ação tomada, se houver]",
            "Observação: [resultado da ação]",
            "",
        ]

        for step in steps:
            parts.append(f"Passo {step.number}: {step.thought}")
            if step.action:
                parts.append(f"Ação: {step.action}")
            if step.observation:
                parts.append(f"Observação: {step.observation}")
            parts.append("")

        parts.append(f"Passo {step_num}:")
        return "\n".join(parts)

    # ── GENERATION ───────────────────────────────────────────
    def _generate(self, prompt: str) -> str:
        if self.llm_fn:
            return self.llm_fn(prompt)
        # Fallback: simples heurística
        return self._fallback_reasoning(prompt)

    def _generate_final_answer(self, question: str, steps: List[ReasoningStep]) -> str:
        prompt = f"Baseado no raciocínio acima, responda à pergunta de forma clara e concisa.\n\nPergunta: {question}\n\nRaciocínio:\n"
        for step in steps:
            prompt += f"- {step.thought}\n"
        prompt += "\nResposta final:"
        return self._generate(prompt)

    def _fallback_reasoning(self, prompt: str) -> str:
        """Fallback quando não há LLM disponível."""
        # Extrai pergunta e tenta resolver heuristicamente
        if "quanto é" in prompt.lower() or "calcule" in prompt.lower():
            numbers = re.findall(r'-?\d+\.?\d*', prompt)
            if len(numbers) >= 2:
                try:
                    a, b = float(numbers[0]), float(numbers[1])
                    if "+" in prompt or "soma" in prompt.lower():
                        return f"Passo: {a} + {b} = {a + b}"
                    if "-" in prompt or "subtra" in prompt.lower():
                        return f"Passo: {a} - {b} = {a - b}"
                    if "*" in prompt or "x" in prompt or "multiplica" in prompt.lower():
                        return f"Passo: {a} × {b} = {a * b}"
                    if "/" in prompt or "divis" in prompt.lower():
                        return f"Passo: {a} ÷ {b} = {a / b if b != 0 else 'indefinido'}"
                except ValueError:
                    pass
        return "Passo: Analisando a informação disponível..."

    # ── PARSING ──────────────────────────────────────────────
    def _parse_step(self, step_num: int, text: str) -> ReasoningStep:
        thought = text
        action = None
        observation = None

        # Try to extract action and observation
        action_match = re.search(r'A[cç][aã]o:\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
        if action_match:
            action = action_match.group(1).strip()
            thought = text[:action_match.start()].strip()

        obs_match = re.search(r'Observa[cç][aã]o:\s*(.+?)(?:\n|$)', text, re.IGNORECASE)
        if obs_match:
            observation = obs_match.group(1).strip()

        # Clean up thought
        thought = re.sub(r'^Passo\s*\d+:\s*', '', thought, flags=re.IGNORECASE).strip()

        return ReasoningStep(
            number=step_num,
            thought=thought,
            action=action,
            observation=observation,
        )

    # ── VERIFICATION ─────────────────────────────────────────
    def _verify_step(self, step: ReasoningStep, question: str, all_steps: List[ReasoningStep]) -> bool:
        """Verifica se o passo é lógico e consistente."""
        # Check for contradictions with previous steps
        for prev in all_steps[:-1]:
            if prev.thought and step.thought:
                # Simple contradiction check
                if self._is_contradictory(prev.thought, step.thought):
                    return False
        return True

    def _is_contradictory(self, thought1: str, thought2: str) -> bool:
        """Detecta contradições simples."""
        t1 = thought1.lower()
        t2 = thought2.lower()
        # Check for direct negation
        negations = [("é", "não é"), ("verdadeiro", "falso"), ("sim", "não"), ("correto", "incorreto")]
        for pos, neg in negations:
            if pos in t1 and neg in t2:
                return True
        return False

    def _score_confidence(self, step: ReasoningStep) -> float:
        """Score de confiança baseado na qualidade do passo."""
        score = 0.5

        # Bonus for specific numbers/facts
        if re.search(r'\d+', step.thought):
            score += 0.1

        # Bonus for clear action
        if step.action:
            score += 0.1

        # Bonus for observation
        if step.observation:
            score += 0.1

        # Penalty for vague language
        vague_words = ["talvez", "possivelmente", "acho que", "maybe", "perhaps", "probably"]
        if any(w in step.thought.lower() for w in vague_words):
            score -= 0.15

        return max(0.0, min(1.0, score))

    def _is_final_answer(self, step: ReasoningStep, step_num: int, max_steps: int) -> bool:
        """Detecta se o passo contém a resposta final."""
        text = step.thought.lower()
        final_indicators = [
            "resposta final", "portanto", "logo", "conclusão",
            "answer is", "therefore", "in conclusion", "final answer",
        ]
        if any(w in text for w in final_indicators):
            return True
        if step_num >= max_steps:
            return True
        return False

    def _build_trace(self, steps: List[ReasoningStep]) -> str:
        lines = []
        for step in steps:
            lines.append(f"Passo {step.number}: {step.thought}")
            if step.action:
                lines.append(f"  → Ação: {step.action}")
            if step.observation:
                lines.append(f"  → Observação: {step.observation}")
        return "\n".join(lines)
