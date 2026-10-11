def build_context(results):
    """
    Converts retrieved document chunks
    into LLM-readable legal context.
    """

    context_parts = []

    for index, (chunk, _) in enumerate(results):

        document = chunk.document

        context_parts.append(
            f"""
Source {index + 1}

Document:
{document.title}

Page:
{chunk.page_number}

Section:
{getattr(chunk, "section", None) or "Not available"}

Content:
{chunk.content[:2000]}
"""
        )

    return "\n\n".join(context_parts)