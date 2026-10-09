import re


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
    document = getattr(chunk, "document", None)
    title = getattr(document, "title", "") if document else ""
    return _normalize_title(title) == _normalize_title(expected_document)


def hit_at_k(results, expected_document):
    """Return 1 if the expected document appears in the retrieved results."""
    return int(
        any(_matches_document(chunk, expected_document) for chunk, _ in results)
    )


def section_hit(results, expected_section):
    """Return 1 if the expected section label is retrieved."""
    expected = _normalize_section(expected_section)
    if not expected:
        return 0

    for chunk, _ in results:
        actual = _normalize_section(getattr(chunk, "section", None))
        if actual and actual == expected:
            return 1

    return 0


def precision_at_k(results, expected_document):
    """Fraction of retrieved chunks whose document matches the expected title."""
    if not results:
        return 0.0

    relevant = sum(
        _matches_document(chunk, expected_document)
        for chunk, _ in results
    )
    return relevant / len(results)


def recall_at_k(results, expected_document):
    """With one expected document label, recall is approximated by hit@k."""
    return hit_at_k(results, expected_document)


def reciprocal_rank(results, expected_document):
    """Return the reciprocal rank of the first result from the expected document."""
    for index, (chunk, _) in enumerate(results, start=1):
        if _matches_document(chunk, expected_document):
            return 1 / index

    return 0.0
