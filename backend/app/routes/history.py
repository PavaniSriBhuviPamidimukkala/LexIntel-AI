from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import require_current_user
from app.database import get_db
from app.models.chat_history import ChatHistory
from app.models.user import User
from app.schemas.history import ChatHistoryResponse


router = APIRouter(
    prefix="/history",
    tags=["History"],
    dependencies=[Depends(require_current_user)],
)


@router.get("/", response_model=list[ChatHistoryResponse])
def get_chat_history(
    current_user: User = Depends(require_current_user),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return (
        db.query(ChatHistory)
        .filter(ChatHistory.user_id == current_user.id)
        .order_by(ChatHistory.created_at.desc(), ChatHistory.id.desc())
        .limit(limit)
        .all()
    )
