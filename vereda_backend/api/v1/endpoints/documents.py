"""
Endpoints de Documentos - Upload e Indexação
=============================================

Upload de arquivos com limites por plano de subscription.
Suporta PDF, TXT, DOCX, MD, HTML.
"""

import os
import uuid
import io
from typing import Optional, List
from datetime import datetime

from fastapi import (
    APIRouter, 
    Depends, 
    HTTPException, 
    status, 
    UploadFile, 
    File,
    Form,
)
from pydantic import BaseModel
from sqlalchemy.orm import Session

from vereda_backend.core.security import get_current_user
from vereda_backend.core.subscription import require_subscription, can_use_feature
from vereda_backend.db import models
from vereda_backend.db.session import get_db
from vereda_backend.core.vector_store_pg import get_vector_store
from vereda_ai.knowledge.document_ingestion import ingest_document, chunk_text


router = APIRouter(prefix="/documents")


# Limites de upload por plano (em MB)
PLAN_UPLOAD_LIMITS = {
    "free": 5,      # 5MB total
    "basic": 50,    # 50MB total
    "medium": 200,  # 200MB total
    "master": 1000, # 1GB total
}

# Limites de documentos por plano
PLAN_DOCUMENT_LIMITS = {
    "free": 3,      # 3 documentos
    "basic": 20,    # 20 documentos
    "medium": 100,  # 100 documentos
    "master": 1000, # 1000 documentos
}

# Limites de chunks por plano
PLAN_CHUNK_LIMITS = {
    "free": 100,    # 100 chunks
    "basic": 500,   # 500 chunks
    "medium": 2000, # 2000 chunks
    "master": 10000, # 10000 chunks
}


class DocumentUploadResponse(BaseModel):
    success: bool
    document_id: str
    filename: str
    chunks_indexed: int
    total_size_mb: float
    message: str


class DocumentListResponse(BaseModel):
    documents: List[dict]
    total: int
    plan_limit: int
    used_space_mb: float
    max_space_mb: int


class DocumentDeleteResponse(BaseModel):
    success: bool
    message: str


def _get_user_plan(user: models.User) -> str:
    """Retorna o plano do usuário."""
    return getattr(user, "subscription_plan", "free") or "free"


def _get_upload_limit_mb(plan: str) -> int:
    """Retorna limite de upload em MB para o plano."""
    return PLAN_UPLOAD_LIMITS.get(plan, PLAN_UPLOAD_LIMITS["free"])


def _get_document_limit(plan: str) -> int:
    """Retorna limite de documentos para o plano."""
    return PLAN_DOCUMENT_LIMITS.get(plan, PLAN_DOCUMENT_LIMITS["free"])


def _get_chunk_limit(plan: str) -> int:
    """Retorna limite de chunks para o plano."""
    return PLAN_CHUNK_LIMITS.get(plan, PLAN_CHUNK_LIMITS["free"])


def _extract_text_from_file(content: bytes, filename: str) -> str:
    """Extrai texto de diferentes tipos de arquivo."""
    suffix = filename.lower().split(".")[-1] if "." in filename else ""
    
    if suffix == "pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(content))
            text_parts = []
            for page in reader.pages:
                text_parts.append(page.extract_text() or "")
            return "\n\n".join(text_parts)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Erro ao extrair PDF: {str(e)}. Instale pypdf: pip install pypdf"
            )
    
    elif suffix in ["txt", "md", "markdown"]:
        return content.decode("utf-8", errors="ignore")
    
    elif suffix == "html" or suffix == "htm":
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, "html.parser")
            return soup.get_text(separator="\n", strip=True)
        except:
            return content.decode("utf-8", errors="ignore")
    
    elif suffix == "docx":
        try:
            import docx
            doc = docx.Document(io.BytesIO(content))
            return "\n\n".join([para.text for para in doc.paragraphs])
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Erro ao extrair DOCX: {str(e)}. Instale python-docx: pip install python-docx"
            )
    
    else:
        # Tentar como texto
        return content.decode("utf-8", errors="ignore")


def _calculate_user_storage(user_id: int, db: Session) -> float:
    """Calcula espaço usado pelo usuário em MB."""
    items = db.query(models.MemoryItem).filter(
        models.MemoryItem.namespace.like(f"user_{user_id}_%"),
        models.MemoryItem.meta.like('%"type": "document"%')
    ).all()
    
    total_bytes = sum(len(item.value.encode("utf-8")) for item in items)
    return total_bytes / (1024 * 1024)


def _count_user_documents(user_id: int, db: Session) -> int:
    """Conta número de documentos do usuário."""
    items = db.query(models.MemoryItem).filter(
        models.MemoryItem.namespace.like(f"user_{user_id}_%"),
        models.MemoryItem.meta.like('%"type": "document"%'),
        models.MemoryItem.key.like("%.meta")  # Metadados do documento
    ).all()
    return len(items)


def _count_user_chunks(user_id: int, db: Session) -> int:
    """Conta número de chunks indexados do usuário."""
    items = db.query(models.MemoryItem).filter(
        models.MemoryItem.namespace.like(f"user_{user_id}_%"),
        models.MemoryItem.key.like("%:chunk_%")
    ).all()
    return len(items)


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    namespace: Optional[str] = Form("default"),
    chunk_size: int = Form(512),
    chunk_overlap: int = Form(64),
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Faz upload e indexa um documento.
    
    Limites por plano:
    - FREE: 3 documentos, 5MB, 100 chunks
    - BASIC: 20 documentos, 50MB, 500 chunks
    - MEDIUM: 100 documentos, 200MB, 2000 chunks
    - MASTER: 1000 documentos, 1GB, 10000 chunks
    """
    # Verificar subscription
    sub_check = require_subscription(db, user, feature="document_upload")
    if not sub_check["allowed"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": sub_check["error"],
                "redirect_url": sub_check.get("redirect_url"),
                "upgrade_required": True,
            }
        )
    
    plan = _get_user_plan(user)
    user_namespace = f"user_{user.id}_{namespace}"
    
    # Validar arquivo
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nome do arquivo inválido")
    
    # Ler conteúdo
    content = await file.read()
    file_size_mb = len(content) / (1024 * 1024)
    
    # Verificar tamanho do arquivo
    max_file_size = min(_get_upload_limit_mb(plan), 50)  # Max 50MB por arquivo
    if file_size_mb > max_file_size:
        raise HTTPException(
            status_code=413,
            detail=f"Arquivo muito grande ({file_size_mb:.1f}MB). Limite: {max_file_size}MB"
        )
    
    # Verificar limite de espaço
    used_space = _calculate_user_storage(user.id, db)
    max_space = _get_upload_limit_mb(plan)
    if used_space + file_size_mb > max_space:
        raise HTTPException(
            status_code=413,
            detail=f"Limite de espaço excedido. Usado: {used_space:.1f}MB/{max_space}MB. Faça upgrade."
        )
    
    # Verificar limite de documentos
    doc_count = _count_user_documents(user.id, db)
    max_docs = _get_document_limit(plan)
    if doc_count >= max_docs:
        raise HTTPException(
            status_code=403,
            detail=f"Limite de documentos atingido ({doc_count}/{max_docs}). Faça upgrade."
        )
    
    # Extrair texto
    try:
        text = _extract_text_from_file(content, file.filename)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Erro ao processar arquivo: {str(e)}"
        )
    
    if not text or len(text.strip()) < 10:
        raise HTTPException(
            status_code=400,
            detail="Arquivo vazio ou sem texto extraível"
        )
    
    # Criar chunks
    chunks = chunk_text(text, chunk_size=chunk_size, overlap=chunk_overlap)
    
    # Verificar limite de chunks
    current_chunks = _count_user_chunks(user.id, db)
    max_chunks = _get_chunk_limit(plan)
    if current_chunks + len(chunks) > max_chunks:
        raise HTTPException(
            status_code=403,
            detail=f"Limite de chunks excedido ({current_chunks}/{max_chunks}). Reduza o arquivo ou faça upgrade."
        )
    
    # Gerar ID único para o documento
    doc_id = f"doc_{uuid.uuid4().hex[:12]}"
    
    # Indexar documento
    vector_store = get_vector_store(db)
    
    # Salvar metadados do documento
    vector_store.add_text(
        namespace=user_namespace,
        doc_id=f"{doc_id}.meta",
        text=text[:1000],  # Primeiros 1000 chars como preview
        metadata={
            "type": "document",
            "filename": file.filename,
            "original_size_mb": file_size_mb,
            "chunks": len(chunks),
            "total_chars": len(text),
            "created_at": datetime.utcnow().isoformat(),
            "user_id": user.id,
        }
    )
    
    # Indexar chunks
    chunks_indexed = 0
    for i, chunk in enumerate(chunks):
        chunk_id = f"{doc_id}:chunk_{i}"
        try:
            vector_store.add_text(
                namespace=user_namespace,
                doc_id=chunk_id,
                text=chunk,
                metadata={
                    "type": "chunk",
                    "document_id": doc_id,
                    "filename": file.filename,
                    "chunk_index": i,
                    "user_id": user.id,
                }
            )
            chunks_indexed += 1
        except Exception as e:
            print(f"Erro ao indexar chunk {i}: {e}")
            continue
    
    return DocumentUploadResponse(
        success=True,
        document_id=doc_id,
        filename=file.filename,
        chunks_indexed=chunks_indexed,
        total_size_mb=file_size_mb,
        message=f"Documento indexado com sucesso. {chunks_indexed} chunks criados.",
    )


@router.get("/list", response_model=DocumentListResponse)
async def list_documents(
    namespace: Optional[str] = None,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Lista documentos do usuário com informações de limites."""
    plan = _get_user_plan(user)
    
    if namespace:
        user_namespace = f"user_{user.id}_{namespace}"
    else:
        # Buscar em todos os namespaces do usuário
        user_namespace = f"user_{user.id}_%"
    
    vector_store = get_vector_store(db)
    
    # Buscar documentos
    if isinstance(vector_store, (PostgreSQLVectorStore, HybridVectorStore)):
        # Listar todos os namespaces
        all_docs = []
        for ns in vector_store._pg_store._cache.keys():
            if ns.startswith(f"user_{user.id}_"):
                docs = vector_store._pg_store.list_documents(ns, user.id)
                for doc in docs:
                    if ".meta" in doc.get("id", ""):
                        all_docs.append(doc)
    else:
        all_docs = []
    
    # Calcular estatísticas
    used_space = _calculate_user_storage(user.id, db)
    max_space = _get_upload_limit_mb(plan)
    doc_count = _count_user_documents(user.id, db)
    max_docs = _get_document_limit(plan)
    
    return DocumentListResponse(
        documents=all_docs,
        total=doc_count,
        plan_limit=max_docs,
        used_space_mb=round(used_space, 2),
        max_space_mb=max_space,
    )


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    namespace: Optional[str] = None,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deleta um documento e seus chunks."""
    user_namespace = f"user_{user.id}_{namespace or 'default'}"
    
    vector_store = get_vector_store(db)
    
    # Deletar metadados
    meta_deleted = vector_store.delete_by_doc_id(user_namespace, f"{document_id}.meta")
    
    # Deletar chunks (precisamos listar primeiro)
    # Buscar todos os chunks deste documento
    chunks = db.query(models.MemoryItem).filter(
        models.MemoryItem.namespace == user_namespace,
        models.MemoryItem.key.like(f"{document_id}:chunk_%")
    ).all()
    
    chunks_deleted = 0
    for chunk in chunks:
        if vector_store.delete_by_doc_id(user_namespace, chunk.key):
            chunks_deleted += 1
    
    if meta_deleted or chunks_deleted > 0:
        return DocumentDeleteResponse(
            success=True,
            message=f"Documento deletado. {chunks_deleted} chunks removidos.",
        )
    else:
        raise HTTPException(status_code=404, detail="Documento não encontrado")


@router.post("/search")
async def search_documents(
    query: str,
    namespace: Optional[str] = None,
    top_k: int = 5,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Busca em documentos indexados."""
    # Verificar subscription
    sub_check = require_subscription(db, user, feature="document_search")
    if not sub_check["allowed"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": sub_check["error"], "redirect_url": sub_check.get("redirect_url")}
        )
    
    if namespace:
        user_namespace = f"user_{user.id}_{namespace}"
    else:
        # Buscar em todos os namespaces
        user_namespace = f"user_{user.id}_default"
    
    vector_store = get_vector_store(db)
    results = vector_store.similarity_search(user_namespace, query, top_k, user.id)
    
    return {
        "query": query,
        "results": results,
        "total": len(results),
    }
