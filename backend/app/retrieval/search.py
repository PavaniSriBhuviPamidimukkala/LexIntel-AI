
import re

from sqlalchemy.orm import Session, joinedload

from app.models.document_chunk import DocumentChunk
from app.models.legal_document import LegalDocument
from app.retrieval.semantic import semantic_search
from app.retrieval.keyword import keyword_search
from app.retrieval.hybrid import hybrid_rank

LEGAL_REFERENCE_PATTERN = re.compile(
    r"\b(section|article)\s+(\d+[a-z]?)\b(?![a-z0-9])",
    re.IGNORECASE,
)
ACT_NAME_PATTERN = re.compile(
    r"\b((?:[a-z0-9&.'()-]+\s+){0,6}"
    r"(?:act|code|regulation))\b",
    re.IGNORECASE,
)
REFERENCE_STOPWORDS = {
    "a", "an", "and", "are", "does", "explain", "for", "in", "is",
    "of", "on", "the", "to", "what", "which",
    "article", "section",
}


def is_retrievable_chunk(chunk):
    """Exclude known boilerplate and unusably short chunks."""
    content = " ".join((chunk.content or "").split())

    if len(content) < 80:
        return False

    if "statutory sample" in content.lower():
        return False

    return True


def get_requested_section(query):
    """Extract an explicit section number without matching longer numbers."""
    match = re.search(
        r"\bsection\s+(\d+[a-z]?)\b(?![a-z0-9])",
        query,
        re.IGNORECASE,
    )
    return match.group(1).lower() if match else None


def get_requested_reference(query):
    """Extract an explicit section or article label and number."""
    match = LEGAL_REFERENCE_PATTERN.search(query)
    if not match:
        return None
    return match.group(1).casefold(), match.group(2).casefold()


def _normalize_words(value):
    return " ".join(re.findall(r"[a-z0-9]+", (value or "").casefold()))


def _reference_matches(value, reference):
    if not value or not reference:
        return False

    label, number = reference
    match = re.search(
        r"\b(section|article)\s*(\d+[a-z]?)\b(?![a-z0-9])",
        str(value),
        re.IGNORECASE,
    )
    return bool(
        match
        and match.group(1).casefold() == label
        and match.group(2).casefold() == number
    )


def chunk_matches_reference(chunk, reference):
    """Check section metadata and text for an exact legal reference."""
    return _reference_matches(
        getattr(chunk, "section", None),
        reference,
    ) or _reference_matches(
        getattr(chunk, "content", None),
        reference,
    )


def chunk_matches_section(chunk, target):
    """Compatibility helper for exact section matching."""
    return chunk_matches_reference(chunk, ("section", target))


def _act_phrases(query):
    phrases = []
    for match in ACT_NAME_PATTERN.finditer(query):
        words = [
            word
            for word in _normalize_words(match.group(1)).split()
            if word not in REFERENCE_STOPWORDS and not word.isdigit()
        ]
        if words and words[-1] in {"act", "code", "regulation"}:
            phrases.append(words)
    return phrases


def _title_acronym(title):
    words = [
        word for word in _normalize_words(title).split()
        if word not in REFERENCE_STOPWORDS
    ]
    return "".join(word[0] for word in words)


def _act_matches_chunk(chunk, query, act_phrases):
    document = getattr(chunk, "document", None)
    title = getattr(document, "title", "") if document else ""
    metadata = getattr(chunk, "metadata_json", None) or {}
    act_name = metadata.get("act_name", "")
    normalized_title = _normalize_words(title)
    normalized_act_name = _normalize_words(act_name)

    for phrase in act_phrases:
        normalized_phrase = " ".join(phrase)
        if (
            normalized_phrase in normalized_title
            or normalized_phrase in normalized_act_name
        ):
            return True

    # Support common legal-document acronyms such as DSA and DPDP(A).
    query_tokens = set(_normalize_words(query).split())
    title_acronym = _title_acronym(title)
    act_acronym = _title_acronym(act_name)
    return any(
        len(token) >= 2
        and (
            title_acronym.startswith(token)
            or act_acronym.startswith(token)
        )
        for token in query_tokens
    )


def metadata_candidate_chunks(chunks, query):
    """
    Narrow chunks by explicit section/article and act-name metadata.

    Exact legal-reference matches take precedence. When both reference and act
    name are supplied, their intersection is preferred when available; if it
    is empty, preserve the exact reference candidates rather than dropping
    potentially relevant passages.
    """
    reference = get_requested_reference(query)
    act_phrases = _act_phrases(query)

    reference_matches = (
        [
            chunk for chunk in chunks
            if chunk_matches_reference(chunk, reference)
        ]
        if reference
        else []
    )
    act_matches = (
        [
            chunk for chunk in chunks
            if _act_matches_chunk(chunk, query, act_phrases)
        ]
        if act_phrases or re.search(r"\b[A-Z]{2,}\b", query)
        else []
    )

    if reference_matches and act_matches:
        combined_matches = [
            chunk for chunk in reference_matches
            if chunk in act_matches
        ]
        return combined_matches or reference_matches
    if reference_matches:
        return reference_matches
    if act_matches:
        return act_matches
    return chunks


def search_documents(
    query: str,
    db: Session,
    user_id: int,
    limit: int = 5,
):
    """Search legal chunks using exact-section preference and hybrid ranking."""
    if limit <= 0:
        return []

    chunks = (
        db.query(DocumentChunk)
        .join(LegalDocument, DocumentChunk.document_id == LegalDocument.id)
        .filter(LegalDocument.user_id == user_id)
        .filter(DocumentChunk.user_id == user_id)
        .options(joinedload(DocumentChunk.document))
        .all()
    )
    chunks = [chunk for chunk in chunks if is_retrievable_chunk(chunk)]

    if not chunks:
        return []

    chunks = metadata_candidate_chunks(chunks, query)
    if not chunks:
        return []

    # Restrict vector distance computation to metadata-matched candidates.
    candidate_ids = [chunk.id for chunk in chunks]
    semantic_scores = semantic_search(
        query,
        db,
        user_id=user_id,
        candidate_ids=candidate_ids,
    )
    keyword_scores = keyword_search(query, chunks)

    return hybrid_rank(
        chunks,
        semantic_scores,
        keyword_scores,
        query=query,
        limit=limit,
        max_per_document=2,
    )