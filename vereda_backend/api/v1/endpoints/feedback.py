from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from vereda_backend.core.security import get_current_user
from vereda_backend.db import models
from vereda_backend.db.session import get_db
from vereda_backend.schemas.feedback import FeedbackCreate, FeedbackPublic
from vereda_backend.services import events


router = APIRouter(prefix="/feedback")


@router.post("", response_model=FeedbackPublic)
def create_feedback(
    payload: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> FeedbackPublic:
    log_row = (
        db.query(models.ConversationLog)
        .filter(models.ConversationLog.id == payload.conversation_log_id)
        .first()
    )
    if not log_row:
        raise ValueError("Conversation não encontrada para feedback.")
    fb = models.Feedback(
        conversation_log_id=payload.conversation_log_id,
        rating=payload.rating,
        comment=payload.comment,
        user_id=current_user.id,
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)

    # Webhook de feedback criado
    events.notify_feedback_created(fb, log_row, current_user)

    return fb


@router.get("", response_model=List[FeedbackPublic])
def list_feedback(
    db: Session = Depends(get_db),
    _: models.User = Depends(get_current_user),
) -> List[FeedbackPublic]:
    rows = (
        db.query(models.Feedback).order_by(models.Feedback.id.desc()).limit(100).all()
    )
    return rows

