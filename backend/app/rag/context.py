def build_context(results):
    """
    Converts retrieved legal documents
    into LLM readable context.
    """

    context_parts = []

    for index, (document, score) in enumerate(results):

        context_parts.append(
            f"""
Source {index + 1}

Title:
{document.title}

Category:
{document.category}

Relevance Score:
{score}

Content:
{document.content[:2000]}
"""
        )

    return "\n\n".join(context_parts)