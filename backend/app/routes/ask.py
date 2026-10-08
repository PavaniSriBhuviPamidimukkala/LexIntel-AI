from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging

from app.database import SessionLocal
from app.rag.pipeline import rag_pipeline
from app.schemas.ask import AskResponse


logger = logging.getLogger(__name__)


router = APIRouter(
    prefix="/ask",
    tags=["RAG"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=AskResponse)
def ask_question(
    question: str,
    db: Session = Depends(get_db)
):

    try:

        return rag_pipeline(
            question,
            db
        )

    except Exception as e:

        logger.exception("RAG pipeline failed")

        raise HTTPException(
            status_code=503,
            detail="AI service is temporarily unavailable. Please try again later."
        )