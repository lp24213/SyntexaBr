"""
VEREDA / SYNTEXA — Hybrid Quantum-Classical Router
====================================================
Roteador híbrido que decide quando usar computação quântica vs clássica.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

log = logging.getLogger(__name__)


class ComputeMode(Enum):
    CLASSICAL = "classical"
    QUANTUM = "quantum"
    HYBRID = "hybrid"


@dataclass
class RoutingDecision:
    mode: ComputeMode
    reason: str
    estimated_speedup: float
    recommended_backend: str


class HybridQuantumRouter:
    """
    Roteador que decide o melhor backend para cada problema.
    """

    def __init__(self, quantum_available: bool = False):
        self.quantum_available = quantum_available
        self._problem_thresholds = {
            "qubo": {"min_vars": 20, "speedup": 2.0},
            "tsp": {"min_cities": 15, "speedup": 1.5},
            "satisfiability": {"min_clauses": 100, "speedup": 3.0},
            "simulation": {"min_qubits": 10, "speedup": 5.0},
        }

    def route(self, problem_type: str, problem_size: int, complexity: float = 1.0) -> RoutingDecision:
        """
        Decide modo de computação baseado no problema.
        """
        threshold = self._problem_thresholds.get(problem_type, {"min_vars": 100, "speedup": 1.0})
        min_size = threshold.get("min_vars", threshold.get("min_cities", 100))
        speedup = threshold.get("speedup", 1.0)

        # Se quantum não disponível, sempre clássico
        if not self.quantum_available:
            return RoutingDecision(
                mode=ComputeMode.CLASSICAL,
                reason="Quantum backend não disponível",
                estimated_speedup=1.0,
                recommended_backend="cpu",
            )

        # Problema pequeno: clássico
        if problem_size < min_size:
            return RoutingDecision(
                mode=ComputeMode.CLASSICAL,
                reason=f"Problema pequeno ({problem_size} < {min_size}), overhead quântico não justifica",
                estimated_speedup=1.0,
                recommended_backend="cpu",
            )

        # Problema médio: híbrido
        if problem_size < min_size * 2:
            return RoutingDecision(
                mode=ComputeMode.HYBRID,
                reason=f"Problema de tamanho intermediário — pré-processamento clássico + otimização quântica",
                estimated_speedup=speedup * 0.5,
                recommended_backend="hybrid_cpu_qpu",
            )

        # Problema grande: quântico
        return RoutingDecision(
            mode=ComputeMode.QUANTUM,
            reason=f"Problema grande ({problem_size} ≥ {min_size}) — benefício quântico significativo",
            estimated_speedup=speedup,
            recommended_backend="qpu",
        )

    def get_recommendation(self, task_description: str) -> Dict[str, Any]:
        """Recomendação baseada em descrição textual."""
        desc_lower = task_description.lower()

        if any(w in desc_lower for w in ["otimiza", "optimize", "qubo", "combinatorial"]):
            return self.route("qubo", 50).__dict__
        elif any(w in desc_lower for w in ["rota", "route", "tsp", "traveling"]):
            return self.route("tsp", 20).__dict__
        elif any(w in desc_lower for w in ["simula", "simulate", "quantum", "molecular"]):
            return self.route("simulation", 20).__dict__
        elif any(w in desc_lower for w in ["satisfiability", "sat", "3sat", "constraint"]):
            return self.route("satisfiability", 200).__dict__
        else:
            return self.route("qubo", 10).__dict__
