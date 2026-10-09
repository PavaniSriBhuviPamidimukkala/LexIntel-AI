
import re

from sqlalchemy.orm import Session

from app.models.document_chunk import DocumentChunk
from app.retrieval.semantic import semantic_search
from app.retrieval.keyword import keyword_search
from app.retrieval.hybrid import hybrid_rank


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


def chunk_matches_section(chunk, target):
    """Check section metadata or text for an exact section reference."""
    if not target:
        return False

    section = str(getattr(chunk, "section", "") or "")
    section_match = re.search(
        r"\bsection\s*(\d+[a-z]?)\b",
        section,
        re.IGNORECASE,
    )

    if section_match and section_match.group(1).lower() == target:
        return True

    content = chunk.content or ""
    content_match = re.search(
        rf"\bsection\s+{re.escape(target)}\b(?![a-z0-9])",
        content,
        re.IGNORECASE,
    )
    return bool(content_match)


def search_documents(
    query: str,
    db: Session,
    limit: int = 5,
):
    """Search legal chunks using exact-section preference and hybrid ranking."""
    if limit <= 0:
        return []

    chunks = db.query(DocumentChunk).all()
    chunks = [chunk for chunk in chunks if is_retrievable_chunk(chunk)]

    if not chunks:
        return []

    semantic_scores = semantic_search(query, db)
    keyword_scores = keyword_search(query, chunks)

    target_section = get_requested_section(query)

    if target_section:
        exact_matches = [
            chunk for chunk in chunks
            if chunk_matches_section(chunk, target_section)
        ]

        # Prefer exact-section chunks when available.
        # Otherwise preserve the normal hybrid-search fallback.
        if exact_matches:
            chunks = exact_matches

    return hybrid_rank(
        chunks,
        semantic_scores,
        keyword_scores,
        query=query,
        limit=limit,
        max_per_document=2,
    )