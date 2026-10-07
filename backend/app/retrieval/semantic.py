from sqlalchemy.orm import Session

from app.models.legal_document import LegalDocument
from app.embeddings.generator import generate_embedding


def semantic_search(
    query: str,
    db: Session
):
    """
    Performs vector similarity search
    using pgvector embeddings.
    """

    query_embedding = generate_embedding(query)

    results = (
        db.query(
            LegalDocument,
            LegalDocument.embedding.cosine_distance(
                query_embedding
            ).label("distance")
        )
        .all()
    )

    semantic_scores = {}

    for document, distance in results:
        semantic_scores[document.id] = 1 - float(distance)

    return semantic_scores