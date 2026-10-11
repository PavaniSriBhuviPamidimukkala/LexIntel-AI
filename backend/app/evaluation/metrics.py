import math
import re


def _result_chunk(result):
    """Accept hybrid (chunk, score) pairs and RAG citation dictionaries."""
    if isinstance(result, dict):
        return result
    return result[0]


def _normalize_title(title):
    """Normalize document titles for case- and whitespace-insensitive matching."""
    return " ".join((title or "").casefold().split())


def _normalize_section(section):
    """Normalize section labels without confusing Section 8 with Section 80."""
    value = " ".join((section or "").casefold().split())
    match = re.search(
        r"\b(section|article|rule|clause)\s*([0-9]+[a-z]?)\b",
        value,
    )
    if match:
        return f"{match.group(1)} {match.group(2)}"

    return re.sub(r"[^a-z0-9]+", " ", value).strip()


def _matches_document(chunk, expected_document):
    if isinstance(chunk, dict):
        title = chunk.get("source", "")
        return _normalize_title(title) == _normalize_title(expected_document)

    document = getattr(chunk, "document", None)
    title = getattr(document, "title", "") if document else ""
    return _normalize_title(title) == _normalize_title(expected_document)


def _matches_chunk(chunk, expected_chunk):
    if isinstance(chunk, dict):
        actual_chunk_id = chunk.get("chunk_id")
        return str(actual_chunk_id) == str(expected_chunk)

    actual_chunk_id = getattr(chunk, "id", None)
    if actual_chunk_id is None:
        actual_chunk_id = getattr(chunk, "chunk_id", None)
    return str(actual_chunk_id) == str(expected_chunk)


def is_relevant(
    chunk,
    expected_document,
    expected_section=None,
    expected_chunk=None,
):
    """Match one benchmark target, narrowing by any supplied labels."""
    if not _matches_document(chunk, expected_document):
        return False

    if expected_section:
        section = (
            chunk.get("section") if isinstance(chunk, dict)
            else getattr(chunk, "section", None)
        )
        actual_section = _normalize_section(section)
        if not actual_section or actual_section != _normalize_section(
            expected_section
        ):
            return False

    if expected_chunk is not None and not _matches_chunk(
        chunk,
        expected_chunk,
    ):
        return False

    return True


def relevant_results(
    results,
    expected_document,
    expected_section=None,
    expected_chunk=None,
):
    """Return retrieved chunks that satisfy the benchmark labels."""
    return [
        chunk
        for result in results
        for chunk in [_result_chunk(result)]
        if is_relevant(
            chunk,
            expected_document,
            expected_section,
            expected_chunk,
        )
    ]


def hit_at_k(results, expected_document):
    """Return 1 if the expected document appears in the retrieved results."""
    return int(any(
        _matches_document(_result_chunk(result), expected_document)
        for result in results
    ))


def section_hit(results, expected_section):
    """Return 1 if the expected section label is retrieved."""
    expected = _normalize_section(expected_section)
    if not expected:
        return 0

    return int(any(
        _normalize_section(
            chunk.get("section") if isinstance(chunk, dict)
            else getattr(chunk, "section", None)
        ) == expected
        for chunk in (_result_chunk(result) for result in results)
    ))


def precision_at_k(
    results,
    expected_document,
    k=5,
    expected_section=None,
    expected_chunk=None,
):
    """Return the fraction of the top K retrieved chunks that are relevant."""
    if k < 1:
        raise ValueError("k must be at least 1")

    relevant_count = len(relevant_results(
        results[:k],
        expected_document,
        expected_section,
        expected_chunk,
    ))
    return relevant_count / k


def recall_at_k(
    results,
    expected_document,
    k=5,
    expected_section=None,
    expected_chunk=None,
):
    """Return whether the single labeled benchmark target appears in top K."""
    if k < 1:
        raise ValueError("k must be at least 1")

    return float(bool(relevant_results(
        results[:k],
        expected_document,
        expected_section,
        expected_chunk,
    )))


def reciprocal_rank(
    results,
    expected_document,
    k=None,
    expected_section=None,
    expected_chunk=None,
):
    """Return the reciprocal rank of the first relevant result."""
    ranked_results = results if k is None else results[:k]
    for index, result in enumerate(ranked_results, start=1):
        chunk = _result_chunk(result)
        if is_relevant(
            chunk,
            expected_document,
            expected_section,
            expected_chunk,
        ):
            return 1 / index

    return 0.0


def ndcg_at_k(
    results,
    expected_document,
    k=5,
    expected_section=None,
    expected_chunk=None,
):
    """Compute nDCG@K with binary relevance from benchmark labels."""
    if k < 1:
        raise ValueError("k must be at least 1")

    relevance = [
        int(is_relevant(
            _result_chunk(result),
            expected_document,
            expected_section,
            expected_chunk,
        ))
        for result in results[:k]
    ]
    dcg = sum(
        rel / math.log2(rank + 1)
        for rank, rel in enumerate(relevance, start=1)
    )

    ideal_relevant_count = min(sum(relevance), k)
    if not ideal_relevant_count:
        return 0.0

    ideal_dcg = sum(
        1 / math.log2(rank + 1)
        for rank in range(1, ideal_relevant_count + 1)
    )
    return dcg / ideal_dcg
