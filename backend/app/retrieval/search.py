from sqlalchemy.orm import Session

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.models.legal_document import LegalDocument
from app.embeddings.generator import generate_embedding


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

    query_embedding = generate_embedding(query)


    semantic_results = (
        db.query(
            LegalDocument,
            LegalDocument.embedding.cosine_distance(
                query_embedding
            ).label("distance")
        )
        .all()
    )


    semantic_scores = {}

    for document, distance in semantic_results:
        semantic_scores[document.id] = 1 - float(distance)



    # -------------------------
    # TF-IDF Keyword Search
    # -------------------------

    corpus = [
        document.content
        for document in documents
    ]


    vectorizer = TfidfVectorizer(
        stop_words="english"
    )


    tfidf_matrix = vectorizer.fit_transform(
        corpus + [query]
    )


    keyword_scores = cosine_similarity(
        tfidf_matrix[-1],
        tfidf_matrix[:-1]
    )[0]



    # -------------------------
    # Hybrid Ranking
    # -------------------------

    results = []


    for index, document in enumerate(documents):

        semantic_score = semantic_scores[document.id]

        keyword_score = float(keyword_scores[index])


        hybrid_score = (
            0.6 * semantic_score
            +
            0.4 * keyword_score
        )


        results.append(
            (
                document,
                hybrid_score
            )
        )


    results.sort(
        key=lambda x: x[1],
        reverse=True
    )


    return results[:limit]
