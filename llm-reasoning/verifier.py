"""
VEREDA / SYNTEXA — Verifier Engine
=====================================
Verificação de respostas com:
- Factual checking
- Consistency verification
- Hallucination detection
- Confidence scoring
"""

import re
import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass

log = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    is_valid: bool
    confidence: float
    issues: List[str]
    facts_checked: int
    hallucination_score: float  # 0-1, menor = melhor
    consistency_score: float    # 0-1, maior = melhor


class VerifierEngine:
    """
    Engine de verificação que valida respostas geradas.
    """

    def __init__(self):
        self._fact_database: Dict[str, Any] = {}
        self._hallucination_patterns = [
            r"eu acho que",
            r"talvez seja",
            r"possivelmente",
            r"não tenho certeza",
            r"acho que sim",
            r"provavelmente é",
            r"deve ser",
            r"i think",
            r"maybe",
            r"probably",
            r"possibly",
            r"i'm not sure",
        ]

    # ── VERIFICATION PIPELINE ────────────────────────────────
    def verify(
        self,
        response: str,
        query: str,
        context: Optional[str] = None,
    ) -> VerificationResult:
        """
        Verifica uma resposta completa.
        """
        issues = []

        # 1. Check hallucinations
        hallucination_score = self._detect_hallucinations(response)
        if hallucination_score > 0.3:
            issues.append(f"Possíveis alucinações detectadas (score: {hallucination_score:.2f})")

        # 2. Check consistency
        consistency_score = self._check_consistency(response, query)
        if consistency_score < 0.5:
            issues.append(f"Resposta inconsistente com a pergunta (score: {consistency_score:.2f})")

        # 3. Check facts
        facts_checked, fact_issues = self._check_facts(response)
        issues.extend(fact_issues)

        # 4. Check completeness
        if not self._is_complete(response, query):
            issues.append("Resposta pode estar incompleta")

        # Calculate overall confidence
        confidence = self._calculate_confidence(
            hallucination_score,
            consistency_score,
            facts_checked,
        )

        is_valid = len(issues) == 0 or (hallucination_score < 0.5 and consistency_score > 0.3)

        return VerificationResult(
            is_valid=is_valid,
            confidence=confidence,
            issues=issues,
            facts_checked=facts_checked,
            hallucination_score=hallucination_score,
            consistency_score=consistency_score,
        )

    # ── HALLUCINATION DETECTION ──────────────────────────────
    def _detect_hallucinations(self, response: str) -> float:
        """
        Detecta padrões indicativos de alucinação.
        Retorna score 0-1 (maior = mais provável alucinação).
        """
        score = 0.0
        response_lower = response.lower()

        # Pattern matching
        for pattern in self._hallucination_patterns:
            if re.search(pattern, response_lower):
                score += 0.15

        # Check for unsupported claims
        unsupported_indicators = [
            "sempre", "nunca", "todos", "todas", "ninguém",
            "100%", "absolutamente", "definitivamente",
            "always", "never", "everyone", "nobody", "absolutely",
        ]
        for indicator in unsupported_indicators:
            if indicator in response_lower:
                score += 0.05

        # Check for fabricated references
        if re.search(r'\[\d+\]|\(\d{4}\)|et al\.', response):
            score += 0.1  # Possible fabricated citation

        # Check for excessive specificity without evidence
        if re.search(r'\b\d{1,2}/\d{1,2}/\d{2,4}\b', response) and "data" not in response_lower:
            score += 0.1  # Random date without context

        return min(1.0, score)

    # ── CONSISTENCY CHECK ────────────────────────────────────
    def _check_consistency(self, response: str, query: str) -> float:
        """Verifica se a resposta é consistente com a pergunta."""
        query_keywords = set(self._extract_keywords(query))
        response_keywords = set(self._extract_keywords(response))

        if not query_keywords:
            return 0.5

        overlap = len(query_keywords & response_keywords)
        coverage = overlap / len(query_keywords)

        # Bonus for direct answers
        if any(w in response.lower() for w in ["resposta", "answer", "conclusão", "conclusion"]):
            coverage += 0.1

        return min(1.0, coverage)

    # ── FACT CHECKING ────────────────────────────────────────
    def _check_facts(self, response: str) -> tuple[int, List[str]]:
        """Verifica fatos numeráveis na resposta."""
        issues = []
        checked = 0

        # Check mathematical claims
        math_patterns = re.findall(r'(\d+)\s*([+\-*/])\s*(\d+)\s*=\s*(\d+)', response)
        for a, op, b, claimed in math_patterns:
            checked += 1
            a, b, claimed = int(a), int(b), int(claimed)
            if op == '+' and a + b != claimed:
                issues.append(f"Erro matemático: {a} + {b} ≠ {claimed}")
            elif op == '-' and a - b != claimed:
                issues.append(f"Erro matemático: {a} - {b} ≠ {claimed}")
            elif op == '*' and a * b != claimed:
                issues.append(f"Erro matemático: {a} × {b} ≠ {claimed}")
            elif op == '/' and b != 0 and a // b != claimed:
                issues.append(f"Erro matemático: {a} ÷ {b} ≠ {claimed}")

        # Check for obviously false statements
        false_patterns = [
            (r'2\s*+\s*2\s*=\s*[^45]', "2+2 deve ser 4"),
            (r'π\s*=\s*[^3]', "π ≈ 3.14159"),
        ]
        for pattern, expected in false_patterns:
            if re.search(pattern, response):
                issues.append(f"Possível erro factual: {expected}")

        return checked, issues

    # ── COMPLETENESS CHECK ───────────────────────────────────
    def _is_complete(self, response: str, query: str) -> bool:
        """Verifica se a resposta parece completa."""
        # Check for incomplete endings
        incomplete_endings = ["e então", "depois", "finalmente", "concluindo", "em resumo"]
        last_50 = response[-50:].lower()
        if any(ending in last_50 for ending in incomplete_endings):
            return False

        # Check length relative to query complexity
        query_words = len(query.split())
        response_words = len(response.split())
        if response_words < query_words * 0.3:
            return False

        return True

    # ── CONFIDENCE CALCULATION ───────────────────────────────
    def _calculate_confidence(
        self,
        hallucination_score: float,
        consistency_score: float,
        facts_checked: int,
    ) -> float:
        """Calcula confiança geral."""
        # Lower hallucination is better
        h_component = 1.0 - hallucination_score
        # Higher consistency is better
        c_component = consistency_score
        # More facts checked increases confidence
        f_component = min(1.0, facts_checked / 5.0)

        return round(0.4 * h_component + 0.4 * c_component + 0.2 * f_component, 3)

    # ── UTILITIES ────────────────────────────────────────────
    def _extract_keywords(self, text: str) -> List[str]:
        words = re.findall(r'\b\w{4,}\b', text.lower())
        stopwords = {"esta", "esse", "aquele", "para", "como", "quando", "onde", "this", "that", "with", "from", "have"}
        return [w for w in words if w not in stopwords]
