"""
Vector Store PostgreSQL + Pinecone/Chroma
==========================================

Persistência real de embeddings no PostgreSQL.
Suporte a múltiplos backends: PostgreSQL, Pinecone, Chroma.
"""

import json
import math
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

from sqlalchemy.orm import Session
from sqlalchemy import text

from vereda_backend.db import models
from vereda_backend.db.session import get_db
from vereda_ai.knowledge.vector_db import VectorDB


# Dimensão dos embeddings
EMBEDDING_DIM = 1536  # OpenAI text-embedding-3-small


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calcula similaridade coseno entre dois vetores."""
    if not a or not b:
        return 0.0
    n = min(len(a), len(b))
    if n <= 0:
        return 0.0
    dot = sum(float(a[i]) * float(b[i]) for i in range(n))
    na = math.sqrt(sum(float(a[i]) ** 2 for i in range(n)))
    nb = math.sqrt(sum(float(b[i]) ** 2 for i in range(n)))
    if na <= 0.0 or nb <= 0.0:
        return 0.0
    return dot / (na * nb)


class PostgreSQLVectorStore(VectorDB):
    """
    Vector store que persiste embeddings no PostgreSQL.
    Usa a tabela memory_items com coluna embedding_vector.
    """
    
    def __init__(
        self,
        db_session: Optional[Session] = None,
        embed_batch_fn: Optional[Callable[[List[str]], List[List[float]]]] = None,
    ):
        self._db = db_session
        self._embed_batch_fn = embed_batch_fn
        self._cache: Dict[str, List[Dict[str, Any]]] = {}
    
    def _get_db(self) -> Session:
        if self._db is not None:
            return self._db
        return next(get_db())
    
    def add_text(
        self,
        namespace: str,
        doc_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Adiciona texto ao vector store PostgreSQL."""
        db = self._get_db()
        
        # Gerar embedding se função disponível
        embedding: Optional[List[float]] = None
        if self._embed_batch_fn and text.strip():
            try:
                batch = self._embed_batch_fn([text])
                if batch and batch[0]:
                    embedding = [float(x) for x in batch[0]]
            except Exception:
                embedding = None
        
        # Verificar se já existe
        existing = db.query(models.MemoryItem).filter(
            models.MemoryItem.key == doc_id,
            models.MemoryItem.namespace == namespace
        ).first()
        
        if existing:
            # Atualizar
            existing.value = text
            existing.meta = json.dumps(metadata or {})
            if embedding:
                existing.embedding_vector = embedding
            existing.updated_at = datetime.utcnow()
        else:
            # Criar novo
            item = models.MemoryItem(
                key=doc_id,
                namespace=namespace,
                value=text,
                meta=json.dumps(metadata or {}),
                embedding_vector=embedding,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(item)
        
        db.commit()
        
        # Atualizar cache
        if namespace not in self._cache:
            self._cache[namespace] = []
        self._cache[namespace].append({
            "id": doc_id,
            "text": text,
            "metadata": metadata or {},
            "embedding": embedding,
        })
    
    def similarity_search(
        self, 
        namespace: str, 
        query: str, 
        top_k: int = 5,
        user_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Busca documentos similares usando embeddings."""
        db = self._get_db()
        
        # Query de embedding
        query_embedding: Optional[List[float]] = None
        if self._embed_batch_fn and query.strip():
            try:
                batch = self._embed_batch_fn([query])
                if batch and batch[0]:
                    query_embedding = [float(x) for x in batch[0]]
            except Exception:
                query_embedding = None
        
        # Buscar todos os itens do namespace
        items = db.query(models.MemoryItem).filter(
            models.MemoryItem.namespace == namespace
        ).all()
        
        if not items:
            return []
        
        scored: List[tuple[float, models.MemoryItem]] = []
        
        # Se temos embedding, usar similaridade coseno
        if query_embedding:
            for item in items:
                if item.embedding_vector:
                    score = _cosine_similarity(query_embedding, item.embedding_vector)
                    if score > 0.3:  # Threshold mínimo
                        scored.append((score, item))
        
        # Fallback: busca por texto (overlap de tokens)
        if not scored:
            query_tokens = set(query.lower().split())
            for item in items:
                text_tokens = set(item.value.lower().split())
                score = len(query_tokens & text_tokens)
                if score > 0:
                    scored.append((float(score), item))
        
        # Ordenar por score
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Retornar top_k
        results: List[Dict[str, Any]] = []
        for score, item in scored[:top_k]:
            meta = {}
            if item.meta:
                try:
                    meta = json.loads(item.meta)
                except:
                    meta = {}
            
            results.append({
                "id": item.key,
                "text": item.value,
                "score": score,
                "metadata": meta,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            })
        
        return results
    
    def delete_by_doc_id(self, namespace: str, doc_id: str) -> bool:
        """Deleta documento pelo ID."""
        db = self._get_db()
        item = db.query(models.MemoryItem).filter(
            models.MemoryItem.key == doc_id,
            models.MemoryItem.namespace == namespace
        ).first()
        
        if item:
            db.delete(item)
            db.commit()
            return True
        return False
    
    def list_documents(
        self, 
        namespace: str,
        user_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Lista todos os documentos de um namespace."""
        db = self._get_db()
        
        items = db.query(models.MemoryItem).filter(
            models.MemoryItem.namespace == namespace
        ).all()
        
        results = []
        for item in items:
            meta = {}
            if item.meta:
                try:
                    meta = json.loads(item.meta)
                except:
                    meta = {}
            
            results.append({
                "id": item.key,
                "text": item.value[:200] + "..." if len(item.value) > 200 else item.value,
                "metadata": meta,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            })
        
        return results


class HybridVectorStore(VectorDB):
    """
    Vector store híbrido: PostgreSQL (primário) + Pinecone/Chroma (opcional)
    """
    
    def __init__(
        self,
        db_session: Optional[Session] = None,
        embed_batch_fn: Optional[Callable[[List[str]], List[List[float]]]] = None,
        pinecone_api_key: Optional[str] = None,
        pinecone_index: Optional[str] = None,
        use_chroma: bool = False,
    ):
        self._pg_store = PostgreSQLVectorStore(db_session, embed_batch_fn)
        self._embed_batch_fn = embed_batch_fn
        self._pinecone_key = pinecone_api_key
        self._pinecone_index = pinecone_index
        self._use_chroma = use_chroma
        self._chroma_client = None
        self._pinecone_index_obj = None
        
        # Inicializar backends extras se configurados
        if pinecone_api_key and pinecone_index:
            self._init_pinecone()
        if use_chroma:
            self._init_chroma()
    
    def _init_pinecone(self):
        """Inicializa conexão com Pinecone."""
        try:
            import pinecone
            pinecone.init(api_key=self._pinecone_key, environment="us-west1-gcp")
            self._pinecone_index_obj = pinecone.Index(self._pinecone_index)
        except Exception as e:
            print(f"Erro ao inicializar Pinecone: {e}")
            self._pinecone_index_obj = None
    
    def _init_chroma(self):
        """Inicializa conexão com Chroma."""
        try:
            import chromadb
            self._chroma_client = chromadb.Client()
        except Exception as e:
            print(f"Erro ao inicializar Chroma: {e}")
            self._chroma_client = None
    
    def add_text(
        self,
        namespace: str,
        doc_id: str,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Adiciona texto em todos os backends disponíveis."""
        # Sempre salvar no PostgreSQL
        self._pg_store.add_text(namespace, doc_id, text, metadata)
        
        # Pinecone
        if self._pinecone_index_obj and self._embed_batch_fn:
            try:
                embedding = self._embed_batch_fn([text])[0]
                self._pinecone_index_obj.upsert(
                    vectors=[(doc_id, embedding, metadata or {})],
                    namespace=namespace,
                )
            except Exception as e:
                print(f"Erro Pinecone: {e}")
        
        # Chroma
        if self._chroma_client and self._embed_batch_fn:
            try:
                collection = self._chroma_client.get_or_create_collection(namespace)
                embedding = self._embed_batch_fn([text])[0]
                collection.add(
                    ids=[doc_id],
                    embeddings=[embedding],
                    documents=[text],
                    metadatas=[metadata or {}],
                )
            except Exception as e:
                print(f"Erro Chroma: {e}")
    
    def similarity_search(
        self, 
        namespace: str, 
        query: str, 
        top_k: int = 5,
        user_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Busca em todos os backends e mergeia resultados."""
        results = self._pg_store.similarity_search(namespace, query, top_k, user_id)
        
        # Se PostgreSQL retornou poucos resultados, tentar outros backends
        if len(results) < top_k:
            # Pinecone
            if self._pinecone_index_obj:
                try:
                    if self._embed_batch_fn:
                        query_emb = self._embed_batch_fn([query])[0]
                        pine_results = self._pinecone_index_obj.query(
                            vector=query_emb,
                            top_k=top_k,
                            namespace=namespace,
                            include_metadata=True,
                        )
                        # Merge resultados
                        for match in pine_results.matches:
                            exists = any(r["id"] == match.id for r in results)
                            if not exists:
                                results.append({
                                    "id": match.id,
                                    "text": match.metadata.get("text", ""),
                                    "score": match.score,
                                    "metadata": match.metadata,
                                    "source": "pinecone",
                                })
                except Exception as e:
                    print(f"Erro Pinecone query: {e}")
            
            # Chroma
            if self._chroma_client:
                try:
                    collection = self._chroma_client.get_or_create_collection(namespace)
                    if self._embed_batch_fn:
                        query_emb = self._embed_batch_fn([query])[0]
                        chroma_results = collection.query(
                            query_embeddings=[query_emb],
                            n_results=top_k,
                        )
                        for i, doc_id in enumerate(chroma_results["ids"][0]):
                            exists = any(r["id"] == doc_id for r in results)
                            if not exists:
                                results.append({
                                    "id": doc_id,
                                    "text": chroma_results["documents"][0][i],
                                    "score": 1.0 - chroma_results["distances"][0][i],
                                    "metadata": chroma_results["metadatas"][0][i] if chroma_results["metadatas"][0] else {},
                                    "source": "chroma",
                                })
                except Exception as e:
                    print(f"Erro Chroma query: {e}")
        
        # Reordenar por score
        results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return results[:top_k]


# Singleton global
def get_vector_store(
    db_session: Optional[Session] = None,
    embed_batch_fn: Optional[Callable[[List[str]], List[List[float]]]] = None,
) -> VectorDB:
    """Retorna instância do vector store configurado."""
    from vereda_backend.core.config import settings
    
    # Usar configurações do settings se disponíveis
    pinecone_key = getattr(settings, "PINECONE_API_KEY", None)
    pinecone_index = getattr(settings, "PINECONE_INDEX", None)
    use_chroma = getattr(settings, "USE_CHROMA", False)
    
    # Se temos Pinecone ou Chroma configurado, usar híbrido
    if pinecone_key or use_chroma:
        return HybridVectorStore(
            db_session=db_session,
            embed_batch_fn=embed_batch_fn,
            pinecone_api_key=pinecone_key,
            pinecone_index=pinecone_index,
            use_chroma=use_chroma,
        )
    
    # Senão, usar apenas PostgreSQL
    return PostgreSQLVectorStore(db_session, embed_batch_fn)
