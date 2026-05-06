# -*- coding: utf-8 -*-
"""Tipos compartilhados para busca híbrida (evita import circular com search_architecture)."""
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SearchResult:
    """Resultado de busca (web, RAG ou API) com metadados de confiabilidade."""
    text: str
    source: str = ""
    confidence: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
