# -*- coding: utf-8 -*-
"""
Yahoo Search: não há API pública estável gratuita alinhada a ToS para scraping em massa.
Para evitar violação de termos/robots, este conector não implementa scraping.
Use busca agregada via DuckDuckGo (já incluída em hybrid) ou API comercial licenciada se necessário.
"""
from __future__ import annotations

from typing import List

from vereda_backend.search.schemas import SearchResult


def search_yahoo(_query: str, _max_results: int = 3) -> List[SearchResult]:
    return []
