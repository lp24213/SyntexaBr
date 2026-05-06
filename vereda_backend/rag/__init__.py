# -*- coding: utf-8 -*-
"""RAG helpers (recuperação, embeddings locais, citações)."""
from vereda_backend.rag.citations import format_search_results_as_citations
from vereda_backend.rag.embeddings_local import embed_texts_local
from vereda_backend.rag.retriever import retrieve_rag_chunks

__all__ = ["embed_texts_local", "retrieve_rag_chunks", "format_search_results_as_citations"]
