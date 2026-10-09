def generate_citations(results):
    """
    Generates legal citations from retrieved chunks.

    Input:
        [
            (DocumentChunk, score)
        ]

    Output:
        [
            {
                "source": "",
                "page": "",
                "chunk_id": "",
                "quote": "",
                "relevance": ""
            }
        ]
    """

    citations = []

    for chunk, score in results:

        citation = {
            "source": chunk.document.title,
            "category": chunk.document.category,
            "page": chunk.page_number,
            "section": chunk.section,
            "chapter": (
                chunk.metadata_json or {}
            ).get("chapter"),
            "chunk_id": chunk.id,
            "quote": chunk.content[:500],
            "relevance": round(float(score), 4)
        }

        citations.append(citation)

    return citations