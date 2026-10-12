import logging
from statistics import mean

from fastapi import APIRouter, Depends
from sqlalchemy import distinct, func, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.evaluation.performance import query_snapshot, timing_snapshot
from app.models.document_chunk import DocumentChunk
from app.models.legal_document import LegalDocument
from app.routes.documents import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["Metrics"])


@router.get("/")
def get_metrics(db: Session = Depends(get_db)):
    query_metrics = query_snapshot()
    timings = timing_snapshot()
    response_times = timings["end_to_end_response_time"]
    retrieval_times = timings["retrieval_latency"]

    metrics = {
        "api_status": "healthy",
        "database_status": "unavailable",
        "total_uploaded_documents": None,
        "total_processed_documents": None,
        "total_chunks": None,
        **query_metrics,
        "average_response_time_seconds": (
            mean(response_times)
            if response_times
            else None
        ),
        "average_retrieval_time_seconds": (
            mean(retrieval_times)
            if retrieval_times
            else None
        ),
        "response_time_history": response_times,
        "retrieval_time_history": retrieval_times,
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
        ).scalar()
        metrics["total_processed_documents"] = db.query(
            func.count(distinct(DocumentChunk.document_id))
        ).scalar()
        metrics["total_chunks"] = db.query(
            func.count(DocumentChunk.id)
        ).scalar()
        metrics["database_status"] = "healthy"
    except SQLAlchemyError:
        logger.exception("Unable to collect database metrics")
        db.rollback()

    return metrics
