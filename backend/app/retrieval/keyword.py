from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def keyword_search(
    query: str,
    documents
):
    """
    Performs keyword based search
    using TF-IDF.
    """

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

    scores = {}

    for index, document in enumerate(documents):
        scores[document.id] = float(
            keyword_scores[index]
        )

    return scores