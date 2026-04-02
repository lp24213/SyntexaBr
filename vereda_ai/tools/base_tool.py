# -*- coding: utf-8 -*-
"""Interface base para tools reutilizáveis."""
from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseTool(ABC):
    """Tool executável pela IA. Independente e reutilizável."""

    name: str = "base"

    @abstractmethod
    def run(self, **kwargs: Any) -> Dict[str, Any]:
        """
        Executa a tool. Retorna dict com 'ok', 'result' ou 'error'.
        """
        ...

    def available(self) -> bool:
        """Se a tool está disponível (ex.: rede para web_tool). Offline-first."""
        return True
