# -*- coding: utf-8 -*-
"""
Research lab API: document ingestion, arXiv search, research mode, math/crypto/quantum tools.
All endpoints extend the existing API; no breaking changes.
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, UploadFile
from pydantic import BaseModel, Field

from vereda_backend.core.security import get_current_user
from vereda_backend.db.session import get_db
from vereda_backend.db import models
from vereda_backend.ai_runtime import (
    rag_engine,
    llm_engine,
    math_engine,
    vector_store,
)
from vereda_ai.research import (
    arxiv_search,
    arxiv_get_abstracts,
    ResearchEngine,
    compress_context,
)
from vereda_ai.research.tool_selector import ToolSelector, ResearchTool
from vereda_ai.knowledge.document_ingestion import ingest_document
from vereda_ai.science.math_ext import MathEngineExt
from vereda_ai.science.crypto_engine import CryptoEngine
from vereda_ai.science.quantum_engine import QuantumEngine


router = APIRouter(prefix="/research")


# --- Schemas ---
class ArxivSearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=512)
    max_results: int = Field(default=10, ge=1, le=50)


class ArxivSearchResponse(BaseModel):
    entries: List[Dict[str, Any]]
    abstracts_text: str


class ResearchQueryRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1024)
    max_web: int = Field(default=6, ge=0, le=20)
    max_arxiv: int = Field(default=5, ge=0, le=20)
    top_k_vector: int = Field(default=5, ge=1, le=30)


class ResearchQueryResponse(BaseModel):
    summary: str
    key_points: List[str]
    paper_references: List[Dict[str, Any]]
    sources: List[str]
    formatted: str


class MathExtRequest(BaseModel):
    operation: str = Field(..., min_length=2, max_length=64)
    params: Dict[str, Any]


class IngestResponse(BaseModel):
    ok: bool
    doc_id: str
    chunks_added: int
    message: str


# --- Lazy init of optional engines (avoid import errors if deps missing) ---
_math_ext: Optional[MathEngineExt] = None
_crypto_engine: Optional[CryptoEngine] = None
_quantum_engine: Optional[QuantumEngine] = None
_research_engine: Optional[ResearchEngine] = None


def _get_math_ext() -> MathEngineExt:
    global _math_ext
    if _math_ext is None:
        _math_ext = MathEngineExt()
    return _math_ext


def _get_crypto_engine() -> CryptoEngine:
    global _crypto_engine
    if _crypto_engine is None:
        _crypto_engine = CryptoEngine()
    return _crypto_engine


def _get_quantum_engine() -> QuantumEngine:
    global _quantum_engine
    if _quantum_engine is None:
        _quantum_engine = QuantumEngine()
    return _quantum_engine


def _get_research_engine() -> ResearchEngine:
    global _research_engine
    if _research_engine is None:
        from vereda_backend.services.search_architecture import web_search
        def _vector_search(ns: str, q: str, k: int):
            if rag_engine and hasattr(rag_engine, "db"):
                return rag_engine.db.similarity_search(namespace=ns, query=q, top_k=k)
            return []
        def _arxiv(q: str, k: int):
            return arxiv_search(q, max_results=k)
        def _summarize(query: str, contexts: List[str]):
            ctx = compress_context(contexts, max_total_tokens=1500)
            messages = [
                {"role": "system", "content": "You are a research assistant. Summarize the following context and list key points."},
                {"role": "user", "content": f"Query: {query}\n\nContext:\n{ctx}"},
            ]
            return llm_engine.chat(messages, max_tokens=500)
        _research_engine = ResearchEngine(
            web_search_fn=web_search,
            vector_search_fn=_vector_search,
            arxiv_search_fn=_arxiv,
            llm_summarize_fn=_summarize,
            max_context_tokens=2048,
        )
    return _research_engine


# --- Endpoints ---
@router.post("/arxiv/search", response_model=ArxivSearchResponse)
async def research_arxiv_search(
    body: ArxivSearchRequest,
    current_user: models.User = Depends(get_current_user),
) -> ArxivSearchResponse:
    """Search arXiv for scientific papers."""
    entries = arxiv_search(body.query, max_results=body.max_results)
    entries_dict = [
        {
            "title": e.title,
            "abstract": e.abstract[:500] + "…" if len(e.abstract) > 500 else e.abstract,
            "arxiv_id": e.arxiv_id,
            "pdf_url": e.pdf_url,
            "authors": e.authors,
            "published": e.published,
        }
        for e in entries
    ]
    abstracts_text = arxiv_get_abstracts(entries)
    return ArxivSearchResponse(entries=entries_dict, abstracts_text=abstracts_text)


@router.post("/arxiv/ingest-to-memory")
async def research_arxiv_ingest(
    body: ArxivSearchRequest,
    current_user: models.User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Search arXiv and store results in vector memory for RAG."""
    entries = arxiv_search(body.query, max_results=min(body.max_results, 5))
    store = rag_engine.db if (rag_engine and hasattr(rag_engine, "db")) else vector_store
    count = 0
    for e in entries:
        text = f"{e.title}\n{e.abstract}"
        store.add_text(
            namespace="arxiv",
            doc_id=e.arxiv_id,
            text=text[:4000],
            metadata={"source": e.pdf_url, "arxiv_id": e.arxiv_id, "title": e.title},
        )
        count += 1
    return {"ok": True, "papers_indexed": count, "namespace": "arxiv"}


@router.post("/query", response_model=ResearchQueryResponse)
async def research_query(
    body: ResearchQueryRequest,
    current_user: models.User = Depends(get_current_user),
) -> ResearchQueryResponse:
    """Run research mode: multi-source search, papers, vector memory, then summarize."""
    engine = _get_research_engine()
    result = engine.run(
        query=body.query,
        top_k_vector=body.top_k_vector,
        max_web=body.max_web,
        max_arxiv=body.max_arxiv,
    )
    formatted = engine.format_output(result)
    return ResearchQueryResponse(
        summary=result.summary,
        key_points=result.key_points,
        paper_references=result.paper_references,
        sources=result.sources,
        formatted=formatted,
    )


_MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB
_ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "text/plain",
    "text/markdown",
    "text/html",
    "application/octet-stream",
}


@router.post("/ingest", response_model=IngestResponse)
async def research_ingest_document(
    file: UploadFile = File(...),
    namespace: str = Form("documents"),
    doc_id: Optional[str] = Form(None),
    current_user: models.User = Depends(get_current_user),
) -> IngestResponse:
    """Ingest a document (PDF, TXT, MD, HTML) into vector store. Max 10 MB."""
    from fastapi import HTTPException, status as http_status

    ct = (file.content_type or "").split(";")[0].strip().lower()
    ext = (file.filename or "").rsplit(".", 1)[-1].lower()
    if ct not in _ALLOWED_CONTENT_TYPES and ext not in ("pdf", "txt", "md", "html", "htm"):
        raise HTTPException(
            status_code=http_status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Tipo de arquivo não suportado. Use PDF, TXT, MD ou HTML.",
        )

    content = await file.read(_MAX_UPLOAD_BYTES + 1)
    if len(content) > _MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=http_status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Arquivo muito grande. Limite: 10 MB.",
        )
    fid = doc_id or (file.filename or "upload").rsplit(".", 1)[0]
    store = rag_engine.db if (rag_engine and hasattr(rag_engine, "db")) else vector_store
    try:
        n = ingest_document(
            vector_store=store,
            content=content,
            doc_id=fid,
            namespace=namespace,
            filename=file.filename,
        )
        return IngestResponse(ok=True, doc_id=fid, chunks_added=n, message=f"Indexed {n} chunks.")
    except Exception as e:
        return IngestResponse(ok=False, doc_id=fid, chunks_added=0, message=str(e))


@router.post("/math/ext")
async def research_math_ext(
    body: MathExtRequest,
    current_user: models.User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Extended math: det, inv, eigenvalues, binom_pmf, normal_cdf, gcd, is_prime, mod_inverse."""
    ext = _get_math_ext()
    op = body.operation.lower()
    p = body.params
    try:
        if op == "det":
            return {"ok": True, "result": ext.det(p["matrix"])}
        if op == "inv":
            return {"ok": True, "result": ext.inv(p["matrix"])}
        if op == "eigenvalues":
            return {"ok": True, "result": [complex(x) for x in ext.eigenvalues(p["matrix"])]}
        if op == "binom_pmf":
            return {"ok": True, "result": ext.binom_pmf(p["n"], p["k"], p["p"])}
        if op == "normal_cdf":
            return {"ok": True, "result": ext.normal_cdf(p["x"], p.get("mu", 0), p.get("sigma", 1))}
        if op == "gcd":
            return {"ok": True, "result": ext.gcd(int(p["a"]), int(p["b"]))}
        if op == "is_prime":
            return {"ok": True, "result": ext.is_prime(int(p["n"]))}
        if op == "mod_inverse":
            out = ext.mod_inverse(int(p["a"]), int(p["m"]))
            return {"ok": True, "result": out}
        return {"ok": False, "error": f"Unknown operation: {op}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/crypto/status")
async def research_crypto_status(
    current_user: models.User = Depends(get_current_user),
) -> Dict[str, bool]:
    """Check if cryptography module is available for RSA/ECC."""
    return {"cryptography_available": _get_crypto_engine().has_cryptography}


@router.post("/crypto/rsa/keypair")
async def research_crypto_rsa_keypair(
    bits: int = 2048,
    current_user: models.User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Generate RSA key pair (PEM)."""
    eng = _get_crypto_engine()
    out = eng.rsa_keypair(bits=bits)
    if out is None:
        return {"ok": False, "error": "cryptography not installed"}
    return {"ok": True, "public_pem": out[0], "private_pem": out[1]}


@router.post("/crypto/ecc/keypair")
async def research_crypto_ecc_keypair(
    current_user: models.User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Generate ECDSA P-256 key pair."""
    eng = _get_crypto_engine()
    out = eng.ecc_keypair()
    if out is None:
        return {"ok": False, "error": "cryptography not installed"}
    return {"ok": True, "public_pem": out[0], "private_pem": out[1]}


@router.get("/quantum/status")
async def research_quantum_status(
    current_user: models.User = Depends(get_current_user),
) -> Dict[str, bool]:
    """Check if Qiskit is available for quantum simulation."""
    return {"qiskit_available": _get_quantum_engine().available}


@router.post("/quantum/bell")
async def research_quantum_bell(
    shots: int = 1024,
    current_user: models.User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Run Bell state simulation."""
    eng = _get_quantum_engine()
    counts = eng.bell_state(shots=shots)
    if counts is None:
        return {"ok": False, "error": "qiskit not installed"}
    return {"ok": True, "counts": counts}
