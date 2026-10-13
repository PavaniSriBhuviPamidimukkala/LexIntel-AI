from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk
from app.models.legal_document import LegalDocument
from app.embeddings.generator import generate_embedding


def semantic_search(
    query: str,
    db: Session,
    user_id: int,
    candidate_ids: list[int] | None = None,
):
    """
    Performs vector similarity search over document chunks.
    """

    query_embedding = generate_embedding(query)

    query_results = (
        db.query(
            DocumentChunk,
            DocumentChunk.embedding.cosine_distance(
                query_embedding
            ).label("distance")
        )
        .join(LegalDocument, DocumentChunk.document_id == LegalDocument.id)
        .filter(DocumentChunk.embedding.isnot(None))
        .filter(LegalDocument.user_id == user_id)
        .filter(DocumentChunk.user_id == user_id)
    )

    if candidate_ids is not None:
        if not candidate_ids:
            return {}
        query_results = query_results.filter(
            DocumentChunk.id.in_(candidate_ids)
        )

    results = query_results.all()

    semantic_scores = {}

    for chunk, distance in results:
        semantic_scores[chunk.id] = 1 - float(distance)

    return semantic_scores