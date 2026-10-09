
import logging
import re

from sqlalchemy.orm import Session

from app.retrieval.search import search_documents
from app.rag.context import build_context
from app.rag.prompts import build_prompt
from app.rag.generator import generate_answer
from app.citations.engine import generate_citations

logger = logging.getLogger(__name__)


def filter_relevant_results(question, results):
    """Filter boilerplate and prioritize an explicitly requested section."""
    cleaned = []

    for chunk, score in results:
        content = " ".join((chunk.content or "").split())

        if len(content) < 80:
            continue

        if "statutory sample" in content.lower():
            continue

        cleaned.append((chunk, score))

    if not cleaned:
        return []

    # Prioritize passages matching an explicitly requested section.
    match = re.search(
        r"\bsection\s+(\d+[a-z]?)\b",
        question,
        re.IGNORECASE,
    )

    if match:
        target = match.group(1).lower()
        exact_matches = []

        for chunk, score in cleaned:
            section = str(getattr(chunk, "section", "") or "")
            content = chunk.content or ""

            section_match = re.search(
                r"\bsection\s*(\d+[a-z]?)\b",
                section,
                re.IGNORECASE,
            )

            content_match = re.search(
                r"\bsection\s+" + re.escape(target) + r"\b",
                content,
                re.IGNORECASE,
            )

            if (
                section_match
                and section_match.group(1).lower() == target
            ) or content_match:
                exact_matches.append((chunk, score))

        if exact_matches:
            return exact_matches

    # This relative threshold is a ranking heuristic, not a probability.
    best_score = max(score for _, score in cleaned)
    threshold = best_score * 0.60

    return [
        (chunk, score)
        for chunk, score in cleaned
        if score >= threshold
    ]


def build_fallback_answer(results):
    """Show useful excerpts when AI generation is unavailable."""

    if not results:
        return (
           "I generation is unavailable, and no relevant document passages "
            "were found. Try rephrasing your question."
        )

    excerpts = []
    seen = set()

    for item in results:
        # Support both (chunk, score) pairs and plain chunk objects.
        if isinstance(item, tuple):
            chunk = item[0]
            score = float(item[1]) if len(item) > 1 else 1.0
        else:
            chunk = item
            score = 1.0

        if score < 0.25:
            continue

        content = " ".join(
            (getattr(chunk, "content", "") or "").split()
        )

        if len(content) < 80:
            continue

        # Exclude known document boilerplate.
        if "statutory sample" in content.lower():
            continue

        # Avoid repeating identical passages.
        normalized = re.sub(
            r"\W+",
            " ",
            content.lower(),
        ).strip()

        if normalized in seen:
            continue

        seen.add(normalized)

        document = getattr(chunk, "document", None)
        title = (
            getattr(document, "title", None)
            or "Uploaded legal document"
        )

        page = getattr(chunk, "page_number", None)
        location = f", page {page}" if page is not None else ""

        # Limit long passages without splitting words.
        excerpt = content

        if len(content) > 900:
            candidate = content[:900]

            # Prefer a complete sentence when a reasonable boundary exists.
            boundary = max(
                candidate.rfind(". "),
                candidate.rfind("? "),
                candidate.rfind("! "),
            )

            if boundary >= 400:
                excerpt = candidate[:boundary + 1]
            else:
                # Otherwise, cut at the last available word boundary.
                boundary = candidate.rfind(" ")

                if boundary > 0:
                    excerpt = candidate[:boundary].rstrip() + "..."
                else:
                    excerpt = candidate.rstrip() + "..."
                # Final safeguard against excerpts ending mid-word or mid-sentence.
        if excerpt and not excerpt.endswith(
            (".", "?", "!", "...", '"', "'", ")", "]")
        ):
            boundary = excerpt.rfind(" ")

            if boundary > 0:
                excerpt = excerpt[:boundary].rstrip() + "..."
        excerpts.append(
            f"Source: {title}{location}\n"
            f"Relevant excerpt: {excerpt}"
        )

        # Return no more than three excerpts.
        if len(excerpts) >= 3:
            break

    if not excerpts:
        return (
            "AI generation is unavailable, and no relevant document "
            "passages were found. Try rephrasing your question."
        )

    return (
        "AI-generated analysis is temporarily unavailable. "
        "The following are excerpts from your uploaded legal documents, "
        "not an AI-generated legal interpretation.\n\n"
        + "\n\n".join(excerpts)
    )


def rag_pipeline(
    question: str,
    db: Session,
    limit: int = 5,
):
    """Retrieve legal passages, generate an answer, and attach citations."""

    retrieved = search_documents(question, db, limit)
    results = filter_relevant_results(question, retrieved)

    if not results:
        return {
            "answer": (
                "No sufficiently relevant passages were found in the "
                "uploaded documents. Try rephrasing your question."
            ),
            "citations": [],
        }

    citations = generate_citations(results)

    context = build_context(results)
    prompt = build_prompt(question, context)

    try:
        answer = generate_answer(prompt)
    except Exception:
        logger.exception("AI answer generation failed")
        answer = build_fallback_answer(results)

    return {
        "answer": answer,
        "citations": citations,
    }