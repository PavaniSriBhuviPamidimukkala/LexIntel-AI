import re


def _available_details(citation):
    details = []

    source = citation.get("source")
    if source is not None and str(source).strip():
        details.append(str(source).strip())

    section = citation.get("section")
    if section is not None and str(section).strip():
        details.append(f"Section: {str(section).strip()}")

    page = citation.get("page")
    if page is not None and str(page).strip():
        details.append(f"Page: {str(page).strip()}")

    return details


def format_citation(citation):
    """Format only source details present in a citation object."""
    details = _available_details(citation)
    return " — ".join(details) if details else "Citation details unavailable"


def format_all_citations(citations):
    """Format citations with stable source numbers matching retrieved context."""
    formatted = []

    for index, citation in enumerate(citations or [], start=1):
        formatted.append(
            f"Source {index}: {format_citation(citation)}"
        )

    return formatted


def _format_evidence(citations):
    evidence = []

    for index, citation in enumerate(citations or [], start=1):
        quote = citation.get("quote")
        if quote is None or not str(quote).strip():
            continue

        details = format_citation(citation)
        evidence.append(
            f"Source {index}: {details}\n"
            f"  {str(quote).strip()}"
        )

    return evidence


def format_answer_with_citations(answer, citations):
    """
    Replace generated source/evidence sections with retrieved citation data.

    Source details and evidence excerpts are always rendered from the original
    citation objects, never from model-generated text.
    """
    answer = (answer or "").strip()
    answer = re.split(
        r"(?im)^\s*(?:#{1,6}\s*)?(?:sources|evidence)\s*:?\s*$",
        answer,
        maxsplit=1,
    )[0].rstrip()

    sources = format_all_citations(citations)
    evidence = _format_evidence(citations)
    if not sources:
        sources = ["No citations are available for this answer."]
    if not evidence:
        evidence = ["No retrieved evidence snippets are available."]

    sections = []
    if answer:
        sections.append(answer)
    sections.extend(
        [
            "Sources:\n" + "\n".join(f"- {source}" for source in sources),
            "Evidence:\n" + "\n".join(f"- {item}" for item in evidence),
        ]
    )
    return "\n\n".join(sections)
