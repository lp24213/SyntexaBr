"""
VEREDA / SYNTEXA — Prompt Optimizer
====================================
Otimização de prompts com:
- Automatic prompt engineering
- Few-shot selection
- Chain-of-thought injection
- Style adaptation
"""

import re
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass
class OptimizedPrompt:
    text: str
    estimated_tokens: int
    technique_applied: str
    confidence: float


class PromptOptimizer:
    """
    Otimizador de prompts que melhora qualidade e reduz tokens.
    """

    # Few-shot exemplos por domínio
    FEW_SHOTS = {
        "code": [
            {"role": "user", "content": "Escreva uma função Python para calcular fibonacci."},
            {"role": "assistant", "content": "```python\ndef fibonacci(n):\n    if n <= 1:\n        return n\n    return fibonacci(n-1) + fibonacci(n-2)\n```"},
        ],
        "reasoning": [
            {"role": "user", "content": "Qual é a raiz quadrada de 144?"},
            {"role": "assistant", "content": "Vou resolver passo a passo:\n1. 12 × 12 = 144\n2. Portanto, √144 = 12"},
        ],
        "summarization": [
            {"role": "user", "content": "Resuma: A inteligência artificial é..."},
            {"role": "assistant", "content": "Resumo: IA refere-se a sistemas..."},
        ],
    }

    # System prompts por modo
    SYSTEM_PROMPTS = {
        "default": "Você é VEREDA, uma IA soberana e inteligente. Responda de forma clara, precisa e útil.",
        "code": "Você é um programador sênior. Escreva código limpo, comentado e eficiente.",
        "reasoning": "Você é um raciocinador lógico. Pense passo a passo e mostre seu raciocínio.",
        "creative": "Você é um criativo. Seja original, inspirador e pense fora da caixa.",
        "technical": "Você é um especialista técnico. Seja preciso, detalhado e rigoroso.",
        "concise": "Você é direto e objetivo. Responda com a menor quantidade de palavras necessária.",
    }

    def __init__(self, default_mode: str = "default"):
        self.default_mode = default_mode

    # ── OPTIMIZATION PIPELINE ────────────────────────────────
    def optimize(
        self,
        prompt: str,
        mode: Optional[str] = None,
        context: Optional[List[Dict[str, str]]] = None,
        add_few_shot: bool = True,
        inject_cot: bool = False,
        max_tokens_target: int = 1024,
    ) -> OptimizedPrompt:
        """
        Pipeline completo de otimização de prompt.
        """
        detected_mode = mode or self._detect_mode(prompt)
        technique = []

        # 1. System prompt
        system = self.SYSTEM_PROMPTS.get(detected_mode, self.SYSTEM_PROMPTS["default"])

        # 2. Few-shot
        few_shot_text = ""
        if add_few_shot and detected_mode in self.FEW_SHOTS:
            few_shot_text = self._format_few_shot(self.FEW_SHOTS[detected_mode])
            technique.append("few_shot")

        # 3. Chain-of-thought injection
        if inject_cot or self._needs_cot(prompt):
            prompt = self._inject_cot(prompt)
            technique.append("cot")

        # 4. Cleanup
        prompt = self._cleanup_prompt(prompt)

        # 5. Assemble
        parts = [f"<|system|>\n{system}"]
        if few_shot_text:
            parts.append(few_shot_text)
        if context:
            for msg in context[-4:]:
                parts.append(f"<|{msg['role']}|>\n{msg['content']}")
        parts.append(f"<|user|>\n{prompt}\n<|assistant|>\n")

        optimized = "\n\n".join(parts)
        est_tokens = len(optimized.split())  # aproximação simples

        return OptimizedPrompt(
            text=optimized,
            estimated_tokens=est_tokens,
            technique_applied=",".join(technique) if technique else "none",
            confidence=0.9 if detected_mode != "default" else 0.7,
        )

    # ── MODE DETECTION ───────────────────────────────────────
    def _detect_mode(self, prompt: str) -> str:
        prompt_lower = prompt.lower()

        code_indicators = ["código", "code", "função", "function", "script", "python", "javascript", "sql", "regex"]
        if any(w in prompt_lower for w in code_indicators):
            return "code"

        reasoning_indicators = ["calcule", "resolva", "explique", "por que", "why", "how to", "passo a passo", "step by step"]
        if any(w in prompt_lower for w in reasoning_indicators):
            return "reasoning"

        creative_indicators = ["crie", "escreva", "poema", "história", "story", "poem", "ideia criativa"]
        if any(w in prompt_lower for w in creative_indicators):
            return "creative"

        technical_indicators = ["explique detalhadamente", "documentação", "arquitetura", "api", "protocolo"]
        if any(w in prompt_lower for w in technical_indicators):
            return "technical"

        return "default"

    # ── FEW-SHOT FORMATTING ──────────────────────────────────
    def _format_few_shot(self, examples: List[Dict[str, str]]) -> str:
        parts = ["<|examples|>"]
        for ex in examples:
            parts.append(f"<|{ex['role']}|>\n{ex['content']}")
        parts.append("<|end_examples|>")
        return "\n".join(parts)

    # ── CHAIN-OF-THOUGHT ─────────────────────────────────────
    def _inject_cot(self, prompt: str) -> str:
        """Adiciona instrução de chain-of-thought ao prompt."""
        cot_prefix = "Pense passo a passo e depois responda: "
        if not prompt.startswith(cot_prefix):
            return cot_prefix + prompt
        return prompt

    def _needs_cot(self, prompt: str) -> bool:
        """Detecta se prompt se beneficia de CoT."""
        math_keywords = ["calcule", "quanto é", "soma", "divisão", "multiplicação", "porcentagem", "equação"]
        logic_keywords = ["se", "então", "logo", "portanto", "prova", "demonstre"]
        prompt_lower = prompt.lower()
        return any(k in prompt_lower for k in math_keywords + logic_keywords)

    # ── CLEANUP ──────────────────────────────────────────────
    def _cleanup_prompt(self, prompt: str) -> str:
        """Limpa formatação desnecessária."""
        # Remove múltiplas quebras de linha
        prompt = re.sub(r'\n{3,}', '\n\n', prompt)
        # Remove espaços múltiplos
        prompt = re.sub(r' {2,}', ' ', prompt)
        # Trim
        prompt = prompt.strip()
        return prompt

    # ── TOKEN ESTIMATION ─────────────────────────────────────
    def estimate_tokens(self, text: str) -> int:
        return len(text.split())
