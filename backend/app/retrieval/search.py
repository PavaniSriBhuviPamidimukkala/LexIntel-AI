from sqlalchemy.orm import Session

from app.models.legal_document import LegalDocument
from app.retrieval.semantic import semantic_search
from app.retrieval.keyword import keyword_search
from app.retrieval.hybrid import hybrid_rank

def search_documents(
    query: str,
    db: Session,
    limit: int = 5
):

    documents = db.query(LegalDocument).all()

    if not documents:
        return []


    # -------------------------
    # Semantic Search (pgvector)
    # -------------------------


    semantic_scores = semantic_search(
        query,
        db
    )


    # -------------------------
    # TF-IDF Keyword Search
    # -------------------------

    keyword_scores = keyword_search(
        query,
        documents
    )   


    # -------------------------
    # Hybrid Ranking
    # -------------------------

    return hybrid_rank(
        documents,
        semantic_scores,
        keyword_scores,
        limit
    )