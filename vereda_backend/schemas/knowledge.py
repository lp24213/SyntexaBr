from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class KnowledgeBaseItemCreate(BaseModel):
    title: str
    question: str
    answer: str
    tags: Optional[str] = ""


class KnowledgeBaseItemPublic(KnowledgeBaseItemCreate):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

