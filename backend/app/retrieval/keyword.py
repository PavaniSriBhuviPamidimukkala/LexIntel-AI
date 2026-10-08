from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def keyword_search(
    query: str,
    chunks
):
    """
    Performs TF-IDF keyword search over document chunks.
    """

    corpus = [
        chunk.content
        for chunk in chunks
    ]

    if not corpus:
        return {}

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

    scores = {}

    for index, chunk in enumerate(chunks):
        scores[chunk.id] = float(
            keyword_scores[index]
        )

    return scores