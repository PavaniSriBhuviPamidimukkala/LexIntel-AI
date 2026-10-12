import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.rag.pipeline import rag_pipeline
from app.schemas.ask import AskResponse
from app.evaluation.performance import record_query, timed_stage

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ask",
    tags=["RAG"],
    dependencies=[Depends(get_current_user)],
)


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

    result = None
    try:
        with timed_stage("end_to_end_response_time"):
            result = rag_pipeline(question.strip(), db)
        return result
    except Exception:
        logger.exception("RAG pipeline failed")
        raise HTTPException(
            status_code=503,
            detail="The legal research service is temporarily unavailable.",
        )
    finally:
        citations = result.get("citations", []) if result else []
        record_query(
            retrieval_succeeded=bool(citations),
            similarity_scores=[
                citation.get("relevance")
                for citation in citations
                if isinstance(citation, dict)
            ],
        )
