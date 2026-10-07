def hybrid_rank(
    documents,
    semantic_scores,
    keyword_scores,
    limit=5
):
    """
    Combines semantic and keyword scores
    and returns ranked documents.
    """

    results = []

    for document in documents:

        semantic_score = semantic_scores.get(
            document.id,
            0
        )

        keyword_score = keyword_scores.get(
            document.id,
            0
        )

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