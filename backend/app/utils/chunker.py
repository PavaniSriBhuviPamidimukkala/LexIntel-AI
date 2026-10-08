import re


def split_text(
    text: str,
    chunk_size: int = 800,
    overlap: int = 150
):

    chunks = []

    start = 0

    text_length = len(text)


    while start < text_length:

        end = start + chunk_size

        chunk = text[start:end]


        if chunk.strip():

            chunks.append(
                chunk.strip()
            )


        start = end - overlap


    return chunks



def extract_legal_metadata(text: str):

    chapter = None
    section = None
    section_title = None


    # Detect chapter

    chapter_match = re.search(
        r"(CHAPTER\s+[IVXLCDM]+\s+[—-].+)",
        text,
        re.IGNORECASE
    )


    if chapter_match:

        chapter = (
            chapter_match
            .group(1)
            .strip()
        )


    # Detect sections

    section_match = re.search(
        r"(\d+)\.\s+([A-Z][^—\n]+)",
        text
    )


    if section_match:

        number = section_match.group(1)

        title = (
            section_match
            .group(2)
            .strip()
        )


        section = (
            f"Section {number}"
        )

        section_title = title



    return {

        "chapter": chapter,

        "section": section,

        "section_title": section_title

    }




def split_pages(
    pages: list[str],
    chunk_size: int = 800,
    overlap: int = 150
):

    """
    Legal aware page chunking.

    Output:

    [
        {
          page_number:1,
          content:"...",
          chapter:"...",
          section:"Section 4",
          section_title:"Grounds for processing..."
        }
    ]

    """

    page_chunks = []


    current_chapter = None
    current_section = None
    current_title = None



    for page_number, page_text in enumerate(
        pages,
        start=1
    ):


        if not page_text.strip():

            continue



        chunks = split_text(
            page_text,
            chunk_size,
            overlap
        )


        for chunk in chunks:


            metadata = extract_legal_metadata(
                chunk
            )


            if metadata["chapter"]:

                current_chapter = (
                    metadata["chapter"]
                )


            if metadata["section"]:

                current_section = (
                    metadata["section"]
                )

                current_title = (
                    metadata["section_title"]
                )



            page_chunks.append(

                {

                    "page_number": page_number,

                    "content": chunk,

                    "chapter": current_chapter,

                    "section": current_section,

                    "section_title": current_title

                }

            )


    return page_chunks