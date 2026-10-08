def build_context(results):
    """
    Converts retrieved document chunks
    into LLM-readable legal context.
    """

    context_parts = []

    for index, (chunk, score) in enumerate(results):

        document = chunk.document

        context_parts.append(
            f"""
Source {index + 1}

Document:
{document.title}

Category:
{document.category}

Page:
{chunk.page_number}

Relevance Score:
{score}

Content:
{chunk.content[:2000]}
"""
        )

    return "\n\n".join(context_parts)