from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.rag.pipeline import rag_pipeline


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



@router.post("/")
def ask_question(
    question: str,
    db: Session = Depends(get_db)
):

    response = rag_pipeline(
        question,
        db
    )

    return response