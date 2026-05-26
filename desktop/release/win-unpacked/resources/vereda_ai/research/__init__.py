# -*- coding: utf-8 -*-
"""Research lab extensions: web search enhancement, arXiv, tool selection, research mode."""
from vereda_ai.research.web_search_enhanced import web_search_cached, rank_and_summarize
from vereda_ai.research.arxiv_client import arxiv_search, arxiv_get_abstracts
from vereda_ai.research.context_compression import compress_context
from vereda_ai.research.tool_selector import ToolSelector, ResearchTool
from vereda_ai.research.research_engine import ResearchEngine

__all__ = [
    "web_search_cached",
    "rank_and_summarize",
    "arxiv_search",
    "arxiv_get_abstracts",
    "compress_context",
    "ToolSelector",
    "ResearchTool",
    "ResearchEngine",
]
