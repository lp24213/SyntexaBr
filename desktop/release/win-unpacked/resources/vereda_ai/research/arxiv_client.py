# -*- coding: utf-8 -*-
"""
arXiv API client for scientific paper search. No API key required.
Lightweight: uses requests + XML parsing (stdlib).
"""
import re
import urllib.request
import urllib.parse
from dataclasses import dataclass
from typing import List, Optional
import xml.etree.ElementTree as ET


@dataclass
class ArxivEntry:
    title: str
    abstract: str
    arxiv_id: str
    pdf_url: str
    authors: List[str]
    published: str
    categories: List[str]


def _parse_atom_entry(entry: ET.Element) -> Optional[ArxivEntry]:
    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
    title_el = entry.find("atom:title", ns)
    summary_el = entry.find("atom:summary", ns)
    id_el = entry.find("atom:id", ns)
    link_pdf = None
    for link in entry.findall("atom:link", ns):
        if link.get("title") == "pdf" or (link.get("href") or "").endswith(".pdf"):
            link_pdf = link.get("href", "")
            break
    authors = []
    for a in entry.findall("atom:author", ns):
        name_el = a.find("atom:name", ns)
        if name_el is not None and name_el.text:
            authors.append(name_el.text.strip())
    published_el = entry.find("atom:published", ns)
    published = published_el.text.strip() if published_el is not None and published_el.text else ""
    categories = []
    for cat in entry.findall("atom:category", ns):
        term = cat.get("term")
        if term:
            categories.append(term)
    if id_el is None or not id_el.text:
        return None
    arxiv_id = id_el.text.strip().split("/")[-1]
    title = title_el.text.strip().replace("\n", " ") if title_el is not None and title_el.text else ""
    abstract = summary_el.text.strip().replace("\n", " ") if summary_el is not None and summary_el.text else ""
    if not link_pdf:
        link_pdf = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    return ArxivEntry(
        title=title,
        abstract=abstract,
        arxiv_id=arxiv_id,
        pdf_url=link_pdf,
        authors=authors,
        published=published,
        categories=categories,
    )


def arxiv_search(
    query: str,
    max_results: int = 10,
    start: int = 0,
) -> List[ArxivEntry]:
    """
    Search arXiv with query. Uses public API (no key).
    """
    base = "http://export.arxiv.org/api/query?"
    params = {
        "search_query": f"all:{query}",
        "start": start,
        "max_results": max_results,
        "sortBy": "relevance",
        "sortOrder": "descending",
    }
    url = base + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            tree = ET.parse(resp)
            root = tree.getroot()
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            entries = root.findall("atom:entry", ns)
            out = []
            for e in entries:
                parsed = _parse_atom_entry(e)
                if parsed:
                    out.append(parsed)
            return out
    except Exception:
        return []


def arxiv_get_abstracts(
    entries: List[ArxivEntry],
    max_chars_per_abstract: int = 1500,
) -> str:
    """Format entries as a single text block for context (summaries + refs)."""
    parts = []
    for i, e in enumerate(entries, 1):
        abs_ = (e.abstract or "")[:max_chars_per_abstract]
        parts.append(f"[{i}] {e.title}\nAbstract: {abs_}\nRef: {e.pdf_url} ({e.arxiv_id})")
    return "\n\n".join(parts)


def arxiv_entries_to_vector_texts(entries: List[ArxivEntry]) -> List[tuple]:
    """Return list of (text, metadata) for adding to vector store."""
    out = []
    for e in entries:
        text = f"{e.title}\n{e.abstract}"
        meta = {"source": e.pdf_url, "arxiv_id": e.arxiv_id, "authors": e.authors, "published": e.published}
        out.append((text, meta))
    return out
