# Research Lab Integration Guide

This document describes the **lightweight AI research laboratory** extensions added to the Syntexa project. All additions are **modular** and **non-breaking**: existing architecture, file names, and routes remain unchanged.

---

## 1. Architecture Overview

```
User Query
    ↓
AI Router (existing PromptRouter)
    ↓
Tool Selection Layer (new: ToolSelector → ResearchTool)
    ↓
Available Tools:
  - Web Search (existing DuckDuckGo + new cache/ranking)
  - Scientific Paper Search (arXiv)
  - Vector Memory Retrieval (existing RAG + optional FAISS)
  - Math Engine (existing + extended: linear algebra, probability, number theory)
  - Cryptography Engine (RSA, ECC, post-quantum experiments)
  - Quantum Simulation Engine (Qiskit)
    ↓
Context Aggregation → Context Compression → LLM Inference → Response
```

---

## 2. New Modules and Folder Placements

| Component | Location | Description |
|-----------|----------|-------------|
| **RAG / Vector** | `vereda_ai/knowledge/vector_db_faiss.py` | Optional FAISS backend implementing `VectorDB` |
| | `vereda_ai/knowledge/document_ingestion.py` | PDF, MD, TXT, HTML → chunks → VectorDB |
| **Web search** | `vereda_ai/cache/web_search_cache.py` | TTL cache for web results |
| | `vereda_ai/research/web_search_enhanced.py` | Cached search + ranking + optional summarization |
| **Scientific** | `vereda_ai/research/arxiv_client.py` | arXiv API: search, abstracts, store in vector memory |
| **Math extension** | `vereda_ai/science/math_ext.py` | det, inv, eigenvalues, binom_pmf, normal_cdf, gcd, is_prime, mod_inverse |
| **Crypto** | `vereda_ai/science/crypto_engine.py` | RSA, ECC keypair/sign/verify, hash-based commitment |
| **Quantum** | `vereda_ai/science/quantum_engine.py` | Qiskit-based simulation (Bell state, custom gates) |
| **Tool selection** | `vereda_ai/research/tool_selector.py` | Heuristic tool selection (no extra LLM call) |
| **Research mode** | `vereda_ai/research/research_engine.py` | Multi-source aggregation + summarization |
| **Context compression** | `vereda_ai/research/context_compression.py` | Truncate/compress context before LLM |
| **Caches** | `vereda_ai/cache/retrieval_cache.py` | TTL cache for vector retrieval |

---

## 3. Integration with Minimal Code Changes

### 3.1 Using FAISS as Vector Backend (optional)

In `vereda_backend/ai_runtime.py` you can **optionally** switch to FAISS when embeddings are available:

```python
# Optional: use FAISS for RAG (requires faiss-cpu and embeddings)
try:
    from vereda_ai.knowledge.vector_db_faiss import FAISSVectorStore
    def _embed_fn(text):
        return llm_engine.embed([text])[0]
    research_vector_store = FAISSVectorStore(embed_fn=_embed_fn, dimension=384)
    # Use research_vector_store for document ingestion; keep vector_store for existing memory
except ImportError:
    research_vector_store = None
```

Do **not** replace the default `vector_store` used by `memory_system` and `rag_engine` unless you migrate all data; use a separate store for research/document ingestion if needed.

### 3.2 Web Search with Cache (optional)

In `vereda_backend/services/chat_engine.py`, you can use cached web search without changing function signatures:

```python
from vereda_ai.research.web_search_enhanced import web_search_cached
from vereda_ai.cache import WebSearchCache
from vereda_backend.services.search_architecture import web_search, SearchResult

# One-time: set cache (e.g. in ai_runtime or at app startup)
from vereda_ai.research.web_search_enhanced import set_web_search_cache
set_web_search_cache(WebSearchCache(ttl_seconds=3600))

# Then replace web_search calls with:
web_results = web_search_cached(content, web_max, search_fn=web_search, result_class=SearchResult)
```

### 3.3 Scientific Connector (arXiv)

The existing `ScientificAPIConnector` in `vereda_backend/services/search_architecture.py` can be wired to arXiv:

```python
# In search_architecture.py, inside ScientificAPIConnector.search:
from vereda_ai.research.arxiv_client import arxiv_search
results = arxiv_search(query, limit=limit)
return [
    SearchResult(text=f"{e.title}: {e.abstract[:500]}", source=e.pdf_url, confidence=0.9, metadata={"arxiv_id": e.arxiv_id})
    for e in results
]
```

---

## 4. Example API Endpoints

All under prefix **`/v1`** (from `settings.api_v1_prefix`).

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/research/arxiv/search` | Search arXiv; returns entries + abstracts text |
| POST | `/v1/research/arxiv/ingest-to-memory` | Search arXiv and index results in vector store |
| POST | `/v1/research/research/query` | Full research mode: web + vector + arxiv → summary |
| POST | `/v1/research/ingest` | Upload document (PDF/TXT/MD/HTML) → vector store |
| POST | `/v1/research/math/ext` | Extended math (det, inv, eigenvalues, binom_pmf, etc.) |
| GET | `/v1/research/crypto/status` | Check if cryptography module available |
| POST | `/v1/research/crypto/rsa/keypair` | Generate RSA key pair |
| POST | `/v1/research/crypto/ecc/keypair` | Generate ECC key pair |
| GET | `/v1/research/quantum/status` | Check if Qiskit available |
| POST | `/v1/research/quantum/bell` | Run Bell state simulation |

### Example: Research query

```bash
curl -X POST "https://api.syntexabr.com.br/v1/research/research/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "recent papers on transformer attention", "max_arxiv": 5}'
```

### Example: Document ingestion

```bash
curl -X POST "https://api.syntexabr.com.br/v1/research/ingest" \
  -F "file=@paper.pdf" \
  -F "namespace=documents" \
  -F "doc_id=my_paper"
```

### Example: Math extension

```bash
curl -X POST "https://api.syntexabr.com.br/v1/research/math/ext" \
  -H "Content-Type: application/json" \
  -d '{"operation": "is_prime", "params": {"n": 97}}'
```

---

## 5. Example Prompts for Research Mode

- *"Search arXiv for papers on quantum error correction and summarize key points."*
- *"Research the latest on transformer architectures and list paper references."*
- *"What do recent papers say about post-quantum cryptography?"*

The research endpoint returns: **Summary**, **Key points**, **Mathematical insights**, **Paper references**, **Sources**.

---

## 6. Dependencies (Optional / Add-On)

Add to `requirements.txt` only if you use the feature:

```text
# Optional: FAISS for vector RAG (CPU)
faiss-cpu>=1.7.4

# Optional: PDF ingestion
pypdf>=3.0.0

# Optional: RSA/ECC cryptography
cryptography>=41.0.0

# Optional: Quantum simulation
qiskit>=1.0.0
qiskit-aer>=0.13.0
```

The project runs **without** these; the new code checks for availability and degrades gracefully.

---

## 7. Performance Optimization Recommendations

- **Quantization**: Use 4-bit or 8-bit quantized models (e.g. Ollama with `q4_0`) to reduce RAM.
- **Context cap**: Compress context to ~2048 tokens before LLM; use `compress_context()` from `vereda_ai.research.context_compression`.
- **Web search cache**: Set `WebSearchCache(ttl_seconds=3600)` and use `web_search_cached()` to avoid repeated DuckDuckGo calls.
- **Retrieval cache**: Use `RetrievalCache(ttl_seconds=600)` when calling `similarity_search` in a loop; check cache before hitting the vector store.
- **Prompt-response cache**: Existing `ResponseCache` in `ModularReasoningEngine` already reduces duplicate LLM calls.
- **Tool selection**: No extra LLM call; `ToolSelector` is keyword-based only.
- **Batch embeddings**: When using FAISS, pass `embed_batch_fn=llm_engine.embed` to embed multiple chunks in one request when the provider supports it.

---

## 8. Low-Memory and CPU Optimization

- **Inference**: Keep using Ollama or vLLM with 4-bit/8-bit quantization as already configured.
- **Context**: Use `compress_context()` from `vereda_ai.research.context_compression` before building the LLM prompt (e.g. cap at 2048 tokens).
- **Caches**: `WebSearchCache` and `RetrievalCache` reduce repeated network and embedding calls.
- **Tool selection**: Heuristic-based (keyword) only; no extra LLM call for tool choice.
- **FAISS**: Use `faiss-cpu`; no GPU required. Dimension 384 matches many small embedding models.

---

## 9. Research Mode Flow (Summary)

1. User sends a query to `/v1/research/research/query`.
2. `ToolSelector` chooses tools (web, vector, arxiv) from keywords.
3. Backend runs web search (existing), vector similarity search (existing RAG store), and arXiv search.
4. Context is aggregated and compressed.
5. Optional LLM summarization produces Summary, Key points, Paper references, Sources.
6. Response is returned in structured form and as formatted markdown.

---

## 10. Constraints Preserved

- **Open-source friendly**: No proprietary APIs required; arXiv and DuckDuckGo are free.
- **Lightweight**: Optional deps; caches in memory; heuristic routing.
- **CPU compatible**: FAISS and Qiskit Aer run on CPU.
- **Hetzner-deployable**: Fits limited RAM; no mandatory GPU.
- **Non-breaking**: No renames or refactors of existing modules; only new files and optional wiring.
