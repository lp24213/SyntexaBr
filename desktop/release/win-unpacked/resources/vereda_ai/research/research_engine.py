# -*- coding: utf-8 -*-
"""
Research mode: multi-source search, paper analysis, math, summarization.
Output format: Summary, Key points, Mathematical insights, Paper references, Sources.
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from vereda_ai.research.tool_selector import ResearchTool, ToolSelector
from vereda_ai.research.context_compression import compress_context


@dataclass
class ResearchResult:
    summary: str = ""
    key_points: List[str] = field(default_factory=list)
    math_insights: List[str] = field(default_factory=list)
    paper_references: List[Dict[str, Any]] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    raw_web: List[Any] = field(default_factory=list)
    raw_arxiv: List[Any] = field(default_factory=list)
    raw_vector: List[Dict[str, Any]] = field(default_factory=list)


class ResearchEngine:
    """
    Orchestrates research mode: run selected tools, aggregate context, optionally call LLM to summarize.
    """

    def __init__(
        self,
        *,
        web_search_fn: Optional[Callable[[str, int], List[Any]]] = None,
        vector_search_fn: Optional[Callable[[str, str, int], List[Dict[str, Any]]]] = None,
        arxiv_search_fn: Optional[Callable[[str, int], List[Any]]] = None,
        math_fn: Optional[Callable[[str], Any]] = None,
        llm_summarize_fn: Optional[Callable[[str, List[str]], str]] = None,
        max_context_tokens: int = 2048,
    ):
        self.web_search_fn = web_search_fn
        self.vector_search_fn = vector_search_fn
        self.arxiv_search_fn = arxiv_search_fn
        self.math_fn = math_fn
        self.llm_summarize_fn = llm_summarize_fn
        self.max_context_tokens = max_context_tokens
        self.tool_selector = ToolSelector()

    def run(
        self,
        query: str,
        tools_override: Optional[List[ResearchTool]] = None,
        namespace: str = "global",
        top_k_vector: int = 5,
        max_web: int = 6,
        max_arxiv: int = 5,
    ) -> ResearchResult:
        """
        Run research pipeline: select tools, gather context, build result.
        If llm_summarize_fn is set, uses it to produce summary and key points.
        """
        result = ResearchResult()
        tools = tools_override or self.tool_selector.select(query)

        snippets: List[str] = []

        if ResearchTool.WEB in tools and self.web_search_fn:
            try:
                web_results = self.web_search_fn(query, max_web)
                for r in web_results:
                    t = getattr(r, "text", str(r)) if not isinstance(r, dict) else r.get("text", "")
                    if t:
                        result.raw_web.append(r)
                        result.sources.append(getattr(r, "source", "") or r.get("source", "web"))
                        snippets.append(t[:800])
            except Exception:
                pass

        if ResearchTool.VECTOR in tools and self.vector_search_fn:
            try:
                docs = self.vector_search_fn(namespace, query, top_k_vector)
                result.raw_vector = docs
                for d in docs:
                    t = d.get("text", "")
                    if t:
                        snippets.append(t[:800])
                        result.sources.append(d.get("source", "vector"))
            except Exception:
                pass

        if ResearchTool.ARXIV in tools and self.arxiv_search_fn:
            try:
                papers = self.arxiv_search_fn(query, max_arxiv)
                result.raw_arxiv = papers
                for p in papers:
                    ref = {"title": getattr(p, "title", ""), "arxiv_id": getattr(p, "arxiv_id", ""), "pdf_url": getattr(p, "pdf_url", "")}
                    result.paper_references.append(ref)
                    text = f"{getattr(p, 'title', '')} {getattr(p, 'abstract', '')}"
                    if text.strip():
                        snippets.append(text[:800])
                        result.sources.append(ref.get("pdf_url", "arxiv"))
            except Exception:
                pass

        context = compress_context(snippets, max_total_tokens=self.max_context_tokens)

        if self.llm_summarize_fn and context:
            result.summary = self.llm_summarize_fn(
                query,
                [context],
            )
            # Heuristic key points: split by newline/sentence (LLM can be prompted to return bullet list)
            result.key_points = [s.strip() for s in result.summary.replace("- ", "\n").split("\n") if len(s.strip()) > 20][:10]
        else:
            result.summary = context[:1500] + ("…" if len(context) > 1500 else "")
            result.key_points = snippets[:5]

        return result

    def format_output(self, result: ResearchResult) -> str:
        """Format ResearchResult as markdown for API/chat response."""
        lines = [
            "## Summary",
            result.summary,
            "",
            "## Key points",
        ]
        for p in result.key_points:
            lines.append(f"- {p}")
        if result.math_insights:
            lines.append("")
            lines.append("## Mathematical insights")
            for m in result.math_insights:
                lines.append(f"- {m}")
        if result.paper_references:
            lines.append("")
            lines.append("## Paper references")
            for ref in result.paper_references:
                title = ref.get("title", "N/A")
                arxiv_id = ref.get("arxiv_id", "")
                url = ref.get("pdf_url", "")
                lines.append(f"- {title} | [{arxiv_id}]({url})")
        if result.sources:
            lines.append("")
            lines.append("## Sources")
            for s in result.sources[:15]:
                if s:
                    lines.append(f"- {s}")
        return "\n".join(lines)
