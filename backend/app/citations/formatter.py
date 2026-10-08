def format_citation(citation):

    return (
        f"[{citation['source']} - "
        f"Page {citation['page']}] "
        f"{citation['quote']}"
    )


def format_all_citations(citations):

    formatted = []

    for citation in citations:
        formatted.append(
            format_citation(citation)
        )

    return formatted