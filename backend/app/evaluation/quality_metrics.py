import re

from app.evaluation.metrics import (
    _normalize_section,
    _normalize_title,
)


TOKEN_PATTERN = re.compile(r"\b[a-z0-9]+\b", re.IGNORECASE)
SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+")
SUPPORT_OVERLAP_THRESHOLD = 0.5

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "in", "is", "it", "of", "on", "or", "that", "the", "this", "to",
    "was", "were", "with",
}


def citation_matches_benchmark(citation, item):
    """Check every citation field supplied by the benchmark."""
    if _normalize_title(citation.get("source")) != _normalize_title(
        item["expected_document"]
    ):
        return False

    expected_page = item.get("expected_page")
    if expected_page is not None and str(citation.get("page")) != str(
        expected_page
    ):
        return False

    expected_section = item.get("expected_section")
    if expected_section and _normalize_section(
        citation.get("section")
    ) != _normalize_section(expected_section):
        return False

    expected_chunk = item.get("expected_chunk")
    if expected_chunk is not None and str(
        citation.get("chunk_id")
    ) != str(expected_chunk):
        return False

    return True


def citation_accuracy(citations, item):
    """Return the fraction of returned citations matching the benchmark."""
    if not citations:
        return 0.0

    correct_citations = sum(
        citation_matches_benchmark(citation, item)
        for citation in citations
    )
    return correct_citations / len(citations)


def _tokens(text):
    return {
        token.casefold()
        for token in TOKEN_PATTERN.findall(text or "")
        if token.casefold() not in STOPWORDS
    }


def source_coverage(citations, expected_evidence):
    """
    Return the fraction of expected evidence terms present in citation quotes.

    Returns None if the benchmark does not provide expected evidence.
    """
    if expected_evidence is None:
        return None

    expected_tokens = _tokens(expected_evidence)
    if not expected_tokens:
        return 0.0

    cited_tokens = set()
    for citation in citations:
        cited_tokens.update(_tokens(citation.get("quote", "")))

    return len(expected_tokens & cited_tokens) / len(expected_tokens)


def _split_claim_sentences(answer):
    return [
        sentence.strip()
        for sentence in SENTENCE_PATTERN.split(answer or "")
        if sentence.strip()
    ]


def _sentence_supported(sentence, citation_tokens):
    claim_tokens = _tokens(sentence)
    if not claim_tokens:
        return True

    overlap = len(claim_tokens & citation_tokens) / len(claim_tokens)
    return overlap >= SUPPORT_OVERLAP_THRESHOLD


def unsupported_claims(answer, citations):
    """
    Count sentences with insufficient lexical overlap with all cited quotes.

    Returns the count and rate; rate is zero when the answer has no sentences.
    """
    sentences = _split_claim_sentences(answer)
    citation_tokens = set()
    for citation in citations:
        citation_tokens.update(_tokens(citation.get("quote", "")))

    unsupported_count = sum(
        not _sentence_supported(sentence, citation_tokens)
        for sentence in sentences
    )
    sentence_count = len(sentences)
    return {
        "unsupported_claim_count": unsupported_count,
        "hallucination_rate": (
            unsupported_count / sentence_count if sentence_count else 0.0
        ),
        "answer_sentence_count": sentence_count,
    }
