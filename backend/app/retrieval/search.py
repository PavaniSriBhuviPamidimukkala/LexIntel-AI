from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk
from app.retrieval.semantic import semantic_search
from app.retrieval.keyword import keyword_search
from app.retrieval.hybrid import hybrid_rank


def search_documents(
    query: str,
    db: Session,
    limit: int = 5
):

    chunks = db.query(DocumentChunk).all()

    if not chunks:
        return []

    semantic_scores = semantic_search(
        query,
        db
    )

    keyword_scores = keyword_search(
        query,
        chunks
    )

    return hybrid_rank(
        chunks,
        semantic_scores,
        keyword_scores,
        limit
    )