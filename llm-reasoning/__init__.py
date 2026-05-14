"""
VEREDA / SYNTEXA — Reasoning Engine
====================================
Sistema de raciocínio avançado com:
- Chain-of-thought
- Planner engine
- Execution engine
- Verifier engine
- Critic engine
- Reflection engine
- Autonomous correction
"""

from .chain_of_thought import ChainOfThoughtEngine
from .planner import PlannerEngine
from .verifier import VerifierEngine
from .critic import CriticEngine
from .reflection import ReflectionEngine
from .reasoning_pipeline import ReasoningPipeline

__all__ = [
    "ChainOfThoughtEngine",
    "PlannerEngine",
    "VerifierEngine",
    "CriticEngine",
    "ReflectionEngine",
    "ReasoningPipeline",
]
