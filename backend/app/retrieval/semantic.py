from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk
from app.embeddings.generator import generate_embedding


def semantic_search(
    query: str,
    db: Session
):
    """
    Performs vector similarity search over document chunks.
    """

    query_embedding = generate_embedding(query)

    results = (
        db.query(
            DocumentChunk,
            DocumentChunk.embedding.cosine_distance(
                query_embedding
            ).label("distance")
        )
        .filter(DocumentChunk.embedding.isnot(None))
        .all()
    )

    semantic_scores = {}

    for chunk, distance in results:
        semantic_scores[chunk.id] = 1 - float(distance)

    return semantic_scores