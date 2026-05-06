# -*- coding: utf-8 -*-
"""Módulo de busca híbrida Syntexa (fontes públicas + ranqueamento)."""
from vereda_backend.search.hybrid import hybrid_public_search
from vereda_backend.search.schemas import SearchResult

__all__ = ["SearchResult", "hybrid_public_search"]
