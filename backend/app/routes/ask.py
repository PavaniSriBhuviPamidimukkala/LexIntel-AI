import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.rag.pipeline import rag_pipeline
from app.schemas.ask import AskResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ask", tags=["RAG"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=AskResponse)
def ask_question(
    question: str = Query(..., min_length=1, max_length=2000),
    db: Session = Depends(get_db),
):
    # Reject empty or whitespace-only questions
    if not question.strip():
        raise HTTPException(
            status_code=422,
            detail="Question cannot be empty or contain only whitespace.",
        )

    try:
        return rag_pipeline(question.strip(), db)
    except Exception:
        logger.exception("RAG pipeline failed")
        raise HTTPException(
            status_code=503,
            detail="The legal research service is temporarily unavailable.",
        )
