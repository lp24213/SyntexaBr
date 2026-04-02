from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class FeedbackCreate(BaseModel):
    conversation_log_id: int
    rating: int
    comment: Optional[str] = None


class FeedbackPublic(BaseModel):
    id: int
    conversation_log_id: int
    rating: int
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

