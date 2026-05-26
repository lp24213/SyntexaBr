# -*- coding: utf-8 -*-
"""
Document ingestion pipeline: PDF, Markdown, TXT, HTML -> text chunks -> VectorDB.
Lightweight extractors; optional dependencies for PDF (pypdf).
"""
import re
from pathlib import Path
from typing import Any, Callable, List, Optional

from vereda_ai.knowledge.vector_db import VectorDB


def extract_text_txt(content: bytes, encoding: str = "utf-8") -> str:
    return content.decode(encoding, errors="replace").strip()


def extract_text_md(content: bytes, encoding: str = "utf-8") -> str:
    return content.decode(encoding, errors="replace").strip()


def extract_text_html(content: bytes, encoding: str = "utf-8") -> str:
    text = content.decode(encoding, errors="replace")
    # Strip tags roughly (no BeautifulSoup dependency by default)
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def extract_text_pdf(content: bytes) -> str:
    try:
        from pypdf import PdfReader
        from io import BytesIO
        reader = PdfReader(BytesIO(content))
        parts = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                parts.append(t)
        return "\n\n".join(parts).strip()
    except ImportError:
        return ""
    except Exception:
        return ""


EXTRACTORS = {
    ".txt": extract_text_txt,
    ".md": extract_text_md,
    ".markdown": extract_text_md,
    ".html": extract_text_html,
    ".htm": extract_text_html,
    ".pdf": extract_text_pdf,
}


def chunk_text(
    text: str,
    chunk_size: int = 512,
    overlap: int = 64,
    separators: Optional[List[str]] = None,
) -> List[str]:
    """Split text into overlapping chunks for embedding. Prefer sentence boundaries."""
    if not text or chunk_size <= 0:
        return []
    separators = separators or ["\n\n", "\n", ". ", " "]
    chunks = []
    remaining = text
    while remaining:
        if len(remaining) <= chunk_size:
            if remaining.strip():
                chunks.append(remaining.strip())
            break
        block = remaining[: chunk_size + 500]
        best_sep = -1
        best_idx = -1
        for sep in separators:
            idx = block.rfind(sep, chunk_size // 2, chunk_size + 200)
            if idx > best_idx:
                best_idx = idx
                best_sep = idx
        if best_sep >= 0:
            chunk = remaining[: best_sep + 1].strip()
            remaining = remaining[best_sep + 1 :].lstrip()
        else:
            chunk = remaining[:chunk_size].strip()
            remaining = remaining[chunk_size:]
        if chunk:
            chunks.append(chunk)
        if overlap and remaining:
            remaining = remaining[overlap:] if len(remaining) > overlap else ""
    return chunks


def ingest_document(
    vector_store: VectorDB,
    content: bytes,
    doc_id: str,
    namespace: str = "documents",
    filename: Optional[str] = None,
    mime_type: Optional[str] = None,
    chunk_size: int = 512,
    overlap: int = 64,
) -> int:
    """
    Extract text from content, chunk it, and add to vector_store.
    Returns number of chunks added. Supports .txt, .md, .html, .pdf (if pypdf installed).
    """
    suffix = ""
    if filename:
        suffix = Path(filename).suffix.lower()
    if mime_type:
        if "pdf" in mime_type:
            suffix = ".pdf"
        elif "html" in mime_type:
            suffix = ".html"
        elif "plain" in mime_type:
            suffix = ".txt"
    extractor = EXTRACTORS.get(suffix, extract_text_txt)
    text = extractor(content)
    if not text:
        return 0
    chunks = chunk_text(text, chunk_size=chunk_size, overlap=overlap)
    source = filename or doc_id
    for i, ch in enumerate(chunks):
        chunk_id = f"{doc_id}:chunk_{i}"
        vector_store.add_text(
            namespace=namespace,
            doc_id=chunk_id,
            text=ch,
            metadata={"source": source, "chunk_index": i},
        )
    return len(chunks)


def ingest_file(
    vector_store: VectorDB,
    path: str | Path,
    namespace: str = "documents",
    doc_id: Optional[str] = None,
    chunk_size: int = 512,
    overlap: int = 64,
) -> int:
    """Read file from path and ingest into vector_store."""
    path = Path(path)
    if not path.exists():
        return 0
    doc_id = doc_id or path.stem
    content = path.read_bytes()
    return ingest_document(
        vector_store,
        content,
        doc_id=doc_id,
        namespace=namespace,
        filename=path.name,
        chunk_size=chunk_size,
        overlap=overlap,
    )
