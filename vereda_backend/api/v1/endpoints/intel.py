from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from vereda_backend.core.security import get_current_user
from vereda_backend.core.syntexa_intel import retrieve_semantic_memory
from vereda_backend.db import models
from vereda_backend.db.session import get_db

router = APIRouter(prefix="/intel")


class MemorySearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=4000)
    top_k: int = Field(default=5, ge=1, le=20)


@router.post("/memory/search")
def search_memory(
    body: MemorySearchRequest,
    db: Session = Depends(get_db),
    current_user: Optional[models.User] = Depends(get_current_user),
) -> dict:
    if not current_user:
        raise HTTPException(status_code=401, detail="Autenticação necessária.")
    hits = retrieve_semantic_memory(
        db,
        user_id=current_user.id,
        query=body.query,
        top_k=body.top_k,
    )
    return {
        "items": [
            {
                "id": x.id,
                "key": x.key,
                "value": x.value,
                "subject": x.subject,
                "sentiment": x.sentiment,
                "updated_at": x.updated_at,
            }
            for x in hits
        ]
    }
