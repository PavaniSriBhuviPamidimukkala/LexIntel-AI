import re
from collections import defaultdict


STOPWORDS = {
    "what", "is", "are", "the", "of", "and", "a", "an",
    "for", "to", "in", "on", "does", "do", "how", "why",
    "act", "law", "section",
}


def _section_matches_query(section, query):
    """Match section identifiers exactly, avoiding Section 8/89 collisions."""
    if not section:
        return False

    match = re.search(
        r"\b(section|article|rule|clause)\s*([0-9]+[a-z]?)\b",
        section.lower(),
    )
    if not match:
        return False

    label, number = match.groups()
    pattern = (
        rf"\b{re.escape(label)}\s*{re.escape(number)}"
        rf"(?![a-z0-9])"
    )
    return re.search(pattern, query.lower()) is not None


def hybrid_rank(
    chunks,
    semantic_scores,
    keyword_scores,
    query,
    limit=5,
    max_per_document=2,
):
    """
    Rank chunks using semantic similarity, keyword matching,
    and modest exact-section/document-title boosts.
    """
    if limit <= 0 or max_per_document <= 0:
        return []

    results = []
    query_words = set(re.findall(r"\b[a-z0-9]+\b", query.lower()))
    meaningful_query_words = query_words - STOPWORDS

    for chunk in chunks:
        semantic_score = semantic_scores.get(chunk.id, 0.0)
        keyword_score = keyword_scores.get(chunk.id, 0.0)

        boost = 0.0

        # Reward an exact section/article reference, not a substring.
        if _section_matches_query(chunk.section, query):
            boost += 0.15

        # Apply a small boost when query terms match title words.
        document = getattr(chunk, "document", None)
        if document and document.title:
            title_words = set(
                re.findall(r"\b[a-z0-9]+\b", document.title.lower())
            )
            if meaningful_query_words & title_words:
                boost += 0.08

        # Reward chunks that cover more meaningful query topic words.
        content = getattr(chunk, "content", "") or ""
        content_words = set(
            re.findall(r"\b[a-z0-9]+\b", content.lower())
        )
        if meaningful_query_words:
            coverage = (
                len(meaningful_query_words & content_words)
                / len(meaningful_query_words)
            )
            boost += 0.24 * coverage

        final_score = (
            0.45 * semantic_score
            + 0.45 * keyword_score
            + boost
        )
        results.append((chunk, final_score))

    results.sort(key=lambda item: item[1], reverse=True)

    final_results = []
    document_counts = defaultdict(int)

    for chunk, score in results:
        document_id = chunk.document_id

        if document_counts[document_id] >= max_per_document:
            continue

        final_results.append((chunk, score))
        document_counts[document_id] += 1

        if len(final_results) >= limit:
            break

    return final_results
