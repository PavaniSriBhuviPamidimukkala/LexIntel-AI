from typing import List, Tuple

from app.models.document_chunk import DocumentChunk


def build_context(
    retrieved_chunks: List[Tuple[DocumentChunk, float]]
) -> str:
    """
    Converts retrieved chunks into a formatted context
    for answer generation.
    """

    if not retrieved_chunks:
        return ""

    context_parts = []

    for index, (chunk, score) in enumerate(
        retrieved_chunks,
        start=1
    ):

        metadata = chunk.metadata_json or {}

        source = metadata.get(
            "act_name",
            "Unknown Source"
        )

        chapter = metadata.get(
            "chapter",
            "N/A"
        )

        section = metadata.get(
            "section",
            "N/A"
        )

        title = metadata.get(
            "section_title",
            ""
        )

        page = chunk.page_number

        context_parts.append(

            f"""
==============================
DOCUMENT {index}
==============================
Source   : {source}
Chapter  : {chapter}
Section  : {section}
Title    : {title}
Page     : {page}
Score    : {score:.3f}

Content:
{chunk.content.strip()}
"""
        )

    return "\n".join(context_parts)