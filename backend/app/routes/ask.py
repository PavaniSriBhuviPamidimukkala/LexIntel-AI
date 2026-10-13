import logging
from math import fsum
from time import perf_counter

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth import require_current_user
from app.database import get_db
from app.models.chat_history import ChatHistory
from app.models.user import User
from app.rag.pipeline import rag_pipeline
from app.schemas.ask import AskResponse
from app.evaluation.performance import capture_timings, timed_stage

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ask",
    tags=["RAG"],
    dependencies=[Depends(require_current_user)],
)


@router.post("/", response_model=AskResponse)
def ask_question(
    question: str = Query(..., min_length=1, max_length=2000),
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    # Reject empty or whitespace-only questions
    if not question.strip():
        raise HTTPException(
            status_code=422,
            detail="Question cannot be empty or contain only whitespace.",
        )

    try:
        with capture_timings() as request_timings:
            started_at = perf_counter()
            with timed_stage("end_to_end_response_time"):
                result = rag_pipeline(
                    question.strip(),
                    db,
                    user_id=current_user.id,
                )
            response_time = perf_counter() - started_at

        citations = result.get("citations", [])
        relevance_scores = [
            float(citation["relevance"])
            for citation in citations
            if isinstance(citation, dict)
            and isinstance(citation.get("relevance"), (int, float))
        ]
        retrieval_times = request_timings.get("retrieval_latency", [])
        history = ChatHistory(
            user_id=current_user.id,
            question=question.strip(),
            answer=result["answer"],
            citations=citations,
            retrieval_succeeded=bool(citations),
            average_similarity_score=(
                fsum(relevance_scores) / len(relevance_scores)
                if relevance_scores
                else None
            ),
            response_time_seconds=response_time,
            retrieval_time_seconds=fsum(retrieval_times),
        )
        db.add(history)
        db.commit()
        return result
    except Exception as exc:
        db.rollback()
        logger.exception("RAG pipeline failed")
        raise HTTPException(
            status_code=503,
            detail="The legal research service is temporarily unavailable.",
        ) from exc
