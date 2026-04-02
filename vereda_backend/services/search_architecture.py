# -*- coding: utf-8 -*-
"""
Arquitetura de busca Syntexa (código próprio).
- RAG: banco vetorial + indexação (já usado em rag_engine/memory_system).
- Web Search Agent: stub para busca em tempo real; filtrar por confiabilidade.
- Conectores: LexML (Brasil), APIs científicas, diários oficiais, bases jurídicas.
Nada do que já existe é removido; este módulo unifica interfaces e extensões.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, List, Optional


# --- RAG: já implementado em ai_runtime (rag_engine, memory_system, vector_store). ---
# Indexação de PDFs/artigos/leis: usar vector_store.add ou rag_engine.db.add quando
# houver pipeline de ingestão. Interface unificada abaixo para futura expansão.


@dataclass
class SearchResult:
    """Resultado de busca (RAG ou web) com metadados de confiabilidade."""
    text: str
    source: str = ""
    confidence: float = 1.0
    metadata: dict = field(default_factory=dict)


def rag_search(
    vector_store: Any,
    query: str,
    namespace: str = "global",
    top_k: int = 5,
) -> List[SearchResult]:
    """Busca vetorial em documentos indexados (RAG). Usa o vector_store já existente."""
    if not hasattr(vector_store, "similarity_search"):
        return []
    docs = vector_store.similarity_search(namespace=namespace, query=query, top_k=top_k)
    return [
        SearchResult(
            text=d.get("text", ""),
            source=d.get("source", "indexed"),
            confidence=float(d.get("score", 1.0)),
            metadata={k: v for k, v in d.items() if k not in ("text", "source", "score")},
        )
        for d in docs
    ]


# --- Web Search Agent: busca real na internet (DuckDuckGo, sem API key). ---


def web_search(query: str, max_results: int = 8) -> List[SearchResult]:
    """Busca em tempo real na web. Usa DuckDuckGo (sem API key). Retorna trechos para contexto."""
    out: List[SearchResult] = []
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                title = r.get("title") or ""
                body = r.get("body") or r.get("snippet") or ""
                href = r.get("href") or ""
                text = f"{title}: {body}".strip()
                if text:
                    out.append(
                        SearchResult(
                            text=text[:800],
                            source=href or "web",
                            confidence=0.9,
                            metadata={"title": title},
                        )
                    )
                if len(out) >= max_results:
                    break
    except Exception:
        pass
    return out


def web_search_available() -> bool:
    """Indica se a busca web está disponível (DuckDuckGo sempre disponível)."""
    return True


# --- Conectores: fontes externas autorizadas (Brasil e científicas). ---


class BaseConnector(ABC):
    """Interface base para conectores de fontes externas."""

    @abstractmethod
    def search(self, query: str, limit: int = 5) -> List[SearchResult]:
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        pass


class LexMLConnector(BaseConnector):
    """Conector para LexML (legislação/jurisprudência Brasil). Stub até configurar API/lexml.gov.br."""

    name = "lexml"

    def search(self, query: str, limit: int = 5) -> List[SearchResult]:
        # TODO: integrar LexML ou API de bases jurídicas licenciadas.
        return []


class ScientificAPIConnector(BaseConnector):
    """Conector para APIs científicas (alternativas legais a SciHub). Stub até configurar."""

    name = "scientific"

    def search(self, query: str, limit: int = 5) -> List[SearchResult]:
        # TODO: integrar PubMed, CrossRef, APIs de repositórios institucionais.
        return []


class DiariosOficiaisConnector(BaseConnector):
    """Conector para diários oficiais (APIs quando disponíveis). Stub."""

    name = "diarios_oficiais"

    def search(self, query: str, limit: int = 5) -> List[SearchResult]:
        # TODO: integrar APIs de DOU ou estaduais.
        return []


# Instâncias para uso no backend (podem ser substituídas por implementações reais).
CONNECTORS = {
    "lexml": LexMLConnector(),
    "scientific": ScientificAPIConnector(),
    "diarios": DiariosOficiaisConnector(),
}


def connector_search(
    connector_key: str,
    query: str,
    limit: int = 5,
) -> List[SearchResult]:
    """Busca via conector nomeado. Retorna lista vazia se conector não existir ou não configurado."""
    conn = CONNECTORS.get(connector_key)
    if not conn:
        return []
    return conn.search(query, limit=limit)


def all_connectors_search(query: str, limit_per: int = 3) -> List[SearchResult]:
    """Dispara busca em todos os conectores e agrega resultados (para análise cruzada)."""
    out: List[SearchResult] = []
    for c in CONNECTORS.values():
        out.extend(c.search(query, limit=limit_per))
    return out
