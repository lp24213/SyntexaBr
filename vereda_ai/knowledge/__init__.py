from vereda_ai.knowledge.vector_db import VectorDB

# `RAGEngine` puxa a cadeia `syntexa_core` (foundation model / torch). Em produção
# o servidor roda em GATEWAY_MODE com embeddings ONNX (sem torch), portanto o import
# precisa ser preguiçoso para não derrubar o boot quando torch não está instalado.
def __getattr__(name):
    if name == "RAGEngine":
        from vereda_ai.knowledge.rag_engine import RAGEngine
        return RAGEngine
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["VectorDB", "RAGEngine"]

