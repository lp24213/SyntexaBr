# -*- coding: utf-8 -*-
"""Interface base para agentes especializados."""
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAgent(ABC):
    """Agente com handle(prompt, context) -> str."""

    name: str = "base"

    @abstractmethod
    def handle(self, prompt: str, context: Dict[str, Any]) -> str:
        """Processa o prompt e retorna a resposta em texto."""
        ...
