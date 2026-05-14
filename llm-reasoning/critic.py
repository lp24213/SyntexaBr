"""
VEREDA / SYNTEXA — Critic Engine
=================================
Engine crítico para avaliação e melhoria iterativa.
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass
class CriticReview:
    score: float  # 0-1
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    overall_verdict: str


class CriticEngine:
    """
    Engine crítico que avalia e sugere melhorias para outputs da IA.
    """

    def review(
        self,
        output: str,
        original_query: str,
        criteria: Optional[List[str]] = None,
    ) -> CriticReview:
        """
        Avalia um output contra critérios.
        """
        criteria = criteria or ["accuracy", "clarity", "completeness", "relevance"]
        strengths = []
        weaknesses = []
        suggestions = []

        # Accuracy
        if "accuracy" in criteria:
            s, w, su = self._check_accuracy(output)
            strengths.extend(s)
            weaknesses.extend(w)
            suggestions.extend(su)

        # Clarity
        if "clarity" in criteria:
            s, w, su = self._check_clarity(output)
            strengths.extend(s)
            weaknesses.extend(w)
            suggestions.extend(su)

        # Completeness
        if "completeness" in criteria:
            s, w, su = self._check_completeness(output, original_query)
            strengths.extend(s)
            weaknesses.extend(w)
            suggestions.extend(su)

        # Relevance
        if "relevance" in criteria:
            s, w, su = self._check_relevance(output, original_query)
            strengths.extend(s)
            weaknesses.extend(w)
            suggestions.extend(su)

        score = self._calculate_score(len(strengths), len(weaknesses))
        verdict = self._verdict(score)

        return CriticReview(
            score=score,
            strengths=strengths,
            weaknesses=weaknesses,
            suggestions=suggestions,
            overall_verdict=verdict,
        )

    def _check_accuracy(self, output: str) -> tuple[List[str], List[str], List[str]]:
        strengths, weaknesses, suggestions = [], [], []

        # Check for specific numbers/dates
        import re
        has_numbers = bool(re.search(r'\d+', output))
        if has_numbers:
            strengths.append("Contém dados específicos")
        else:
            suggestions.append("Adicionar dados quantitativos quando possível")

        # Check for citations/references
        has_refs = bool(re.search(r'\[.*?\]|\(.*?\d{4}.*?\)', output))
        if has_refs:
            strengths.append("Inclui referências")
        else:
            suggestions.append("Adicionar fontes quando apropriado")

        return strengths, weaknesses, suggestions

    def _check_clarity(self, output: str) -> tuple[List[str], List[str], List[str]]:
        strengths, weaknesses, suggestions = [], [], []

        sentences = output.split('.')
        avg_len = sum(len(s) for s in sentences) / max(len(sentences), 1)

        if avg_len < 100:
            strengths.append("Sentenças concisas")
        else:
            weaknesses.append("Sentenças muito longas")
            suggestions.append("Dividir sentenças complexas em partes menores")

        # Check structure
        if '\n' in output or '-' in output or '1.' in output:
            strengths.append("Boa estruturação visual")
        else:
            suggestions.append("Usar listas ou parágrafos para melhorar legibilidade")

        return strengths, weaknesses, suggestions

    def _check_completeness(self, output: str, query: str) -> tuple[List[str], List[str], List[str]]:
        strengths, weaknesses, suggestions = [], [], []

        query_lower = query.lower()
        output_lower = output.lower()

        # Check if all question words are addressed
        question_words = ["quem", "o que", "onde", "quando", "por que", "como", "quanto", "who", "what", "where", "when", "why", "how"]
        for qw in question_words:
            if qw in query_lower and qw not in output_lower:
                weaknesses.append(f"Não endereça explicitamente '{qw}'")
                suggestions.append(f"Responda explicitamente à pergunta sobre '{qw}'")

        # Check length
        if len(output.split()) < 20:
            weaknesses.append("Resposta muito curta")
            suggestions.append("Expandir a resposta com mais detalhes")
        elif len(output.split()) > 500:
            suggestions.append("Considerar resumir para maior clareza")

        return strengths, weaknesses, suggestions

    def _check_relevance(self, output: str, query: str) -> tuple[List[str], List[str], List[str]]:
        strengths, weaknesses, suggestions = [], [], []

        import re
        query_keywords = set(re.findall(r'\b\w{4,}\b', query.lower()))
        output_keywords = set(re.findall(r'\b\w{4,}\b', output.lower()))

        overlap = len(query_keywords & output_keywords)
        if overlap > 0:
            strengths.append(f"Relevante ao tema ({overlap} keywords em comum)")
        else:
            weaknesses.append("Pouca relevância com a pergunta")
            suggestions.append("Conectar mais explicitamente à pergunta original")

        return strengths, weaknesses, suggestions

    def _calculate_score(self, strengths: int, weaknesses: int) -> float:
        total = strengths + weaknesses
        if total == 0:
            return 0.5
        return round(strengths / total, 2)

    def _verdict(self, score: float) -> str:
        if score >= 0.8:
            return "Excelente — pronto para uso"
        elif score >= 0.6:
            return "Bom — pequenas melhorias sugeridas"
        elif score >= 0.4:
            return "Regular — revisão recomendada"
        else:
            return "Insuficiente — requer reescrita"
