import re
from collections import defaultdict


STOPWORDS = {
    "what", "is", "are", "the", "of", "and", "a", "an",
    "for", "to", "in", "on", "does", "do", "how", "why",
    "act", "law", "section",
}

SECTION_DIVERSITY_SCORE_RATIO = 0.9
CONTENT_OVERLAP_THRESHOLD = 0.8
MIN_OVERLAP_TOKENS = 5


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


def _normalized_content(chunk):
    return " ".join((getattr(chunk, "content", "") or "").split())


def _content_tokens(chunk):
    return {
        token
        for token in re.findall(
            r"\b[a-z0-9]+\b",
            _normalized_content(chunk).lower(),
        )
        if token not in STOPWORDS
    }


def _substantially_overlaps(chunk, selected_chunks):
    candidate_tokens = _content_tokens(chunk)
    if len(candidate_tokens) < MIN_OVERLAP_TOKENS:
        return False

    for selected_chunk in selected_chunks:
        selected_tokens = _content_tokens(selected_chunk)
        if len(selected_tokens) < MIN_OVERLAP_TOKENS:
            continue

        shared_tokens = len(candidate_tokens & selected_tokens)
        smaller_content_size = min(
            len(candidate_tokens),
            len(selected_tokens),
        )

        # Compare against the smaller token set so a short passage contained
        # in a larger chunk is recognized as overlap too.
        if (
            shared_tokens / smaller_content_size
            >= CONTENT_OVERLAP_THRESHOLD
        ):
            return True

    return False


def _section_key(chunk):
    section = str(getattr(chunk, "section", "") or "").strip().lower()
    return section or None


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

        # Remove weakly relevant legal passages
    MIN_SCORE = 0.30

    results = [
        (chunk, score)
        for chunk, score in results
        if score >= MIN_SCORE
    ]

    seen_content = set()
    unique_results = []

    for chunk, score in results:
        content = _normalized_content(chunk)
        if content in seen_content:
            continue

        # Results are score-sorted, so the first chunk with this normalized
        # content is the highest-scoring copy. Mark it seen even if the
        # per-document cap later excludes it, so a lower-scoring duplicate
        # from another document cannot be returned instead.
        seen_content.add(content)
        unique_results.append((chunk, score))

    final_results = []
    document_counts = defaultdict(int)
    selected_sections = set()

    while unique_results and len(final_results) < limit:
        eligible_results = [
            (chunk, score)
            for chunk, score in unique_results
            if document_counts[chunk.document_id] < max_per_document
            and not _substantially_overlaps(
                chunk,
                [selected_chunk for selected_chunk, _ in final_results],
            )
        ]
        if not eligible_results:
            break

        highest_score = eligible_results[0][1]
        similar_relevance_cutoff = (
            highest_score * SECTION_DIVERSITY_SCORE_RATIO
        )

        # Preserve the score ordering for close competitors while preferring
        # another section within 10% of the best eligible result.
        selected_result = next(
            (
                (chunk, score)
                for chunk, score in eligible_results
                if score >= similar_relevance_cutoff
                and _section_key(chunk) is not None
                and _section_key(chunk) not in selected_sections
            ),
            eligible_results[0],
        )

        chunk, score = selected_result
        unique_results.remove(selected_result)
        final_results.append((chunk, score))
        document_counts[chunk.document_id] += 1

        section = _section_key(chunk)
        if section is not None:
            selected_sections.add(section)

    # Diversity affects which chunks are selected, not their ranking order.
    final_results.sort(key=lambda item: item[1], reverse=True)

    return final_results
