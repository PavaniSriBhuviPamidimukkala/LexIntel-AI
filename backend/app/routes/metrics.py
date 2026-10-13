import logging
from statistics import mean

from fastapi import APIRouter, Depends
from sqlalchemy import distinct, func, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth import require_current_user
from app.core.config import settings
from app.models.chat_history import ChatHistory
from app.models.document_chunk import DocumentChunk
from app.models.legal_document import LegalDocument
from app.models.user import User
from app.routes.documents import get_db

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/metrics",
    tags=["Metrics"],
    dependencies=[Depends(require_current_user)],
)


@router.get("/")
def get_metrics(
    current_user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
):
    metrics = {
        "api_status": "healthy",
        "database_status": "unavailable",
        "total_uploaded_documents": None,
        "total_processed_documents": None,
        "total_chunks": None,
        "total_queries_asked": None,
        "retrieval_success_count": None,
        "average_similarity_score": None,
        "average_response_time_seconds": None,
        "average_retrieval_time_seconds": None,
        "response_time_history": [],
        "retrieval_time_history": [],
        "system_information": {
            "frontend": "React + Vite",
            "backend": "FastAPI",
            "database": "PostgreSQL + pgvector",
            "embedding_model": settings.EMBEDDING_MODEL,
            "llm": (
                settings.GEMINI_MODEL
                if settings.LLM_PROVIDER.casefold() == "gemini"
                else settings.OLLAMA_MODEL
            ),
            "retrieval_method": "Hybrid semantic + keyword",
        },
    }

    try:
        db.execute(text("SELECT 1"))
        metrics["total_uploaded_documents"] = db.query(
            func.count(LegalDocument.id)
        ).filter(LegalDocument.user_id == current_user.id).scalar()
        metrics["total_processed_documents"] = db.query(
            func.count(distinct(DocumentChunk.document_id))
        ).join(
            LegalDocument,
            DocumentChunk.document_id == LegalDocument.id,
        ).filter(
            LegalDocument.user_id == current_user.id
        ).filter(
            DocumentChunk.user_id == current_user.id
        ).scalar()
        metrics["total_chunks"] = db.query(
            func.count(DocumentChunk.id)
        ).join(
            LegalDocument,
            DocumentChunk.document_id == LegalDocument.id,
        ).filter(
            LegalDocument.user_id == current_user.id
        ).filter(
            DocumentChunk.user_id == current_user.id
        ).scalar()

        user_history = (
            db.query(ChatHistory)
            .filter(ChatHistory.user_id == current_user.id)
            .order_by(ChatHistory.created_at)
            .all()
        )
        response_times = [
            item.response_time_seconds for item in user_history
        ]
        retrieval_times = [
            item.retrieval_time_seconds for item in user_history
        ]
        similarity_scores = [
            item.average_similarity_score
            for item in user_history
            if item.average_similarity_score is not None
        ]
        metrics.update({
            "total_queries_asked": len(user_history),
            "retrieval_success_count": sum(
                item.retrieval_succeeded for item in user_history
            ),
            "average_similarity_score": (
                round(mean(similarity_scores), 6)
                if similarity_scores
                else None
            ),
            "average_response_time_seconds": (
                mean(response_times) if response_times else None
            ),
            "average_retrieval_time_seconds": (
                mean(retrieval_times) if retrieval_times else None
            ),
            "response_time_history": response_times,
            "retrieval_time_history": retrieval_times,
        })
        metrics["database_status"] = "healthy"
    except SQLAlchemyError:
        logger.exception("Unable to collect database metrics")
        db.rollback()

    return metrics
