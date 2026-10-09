import re


def clean_pdf_text(text: str) -> str:
    """Remove common PDF extraction noise and repair word joins."""

    if not text:
        return ""

    # Remove page markers
    text = re.sub(
        r"Page\s+\d+\s+of\s+\d+",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # Remove unwanted sample headers
    text = re.sub(
        r"(?im)^\s*Statutory\s+Sample\b[^\n]*(?:\n|$)",
        "",
        text,
    )

    # Normalize spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Remove hidden PDF characters
    text = text.replace("\u00a0", " ")
    text = text.replace("\u200b", "")
    text = text.replace("\ufeff", "")

    # Repair PDF extraction word joins
    # Examples:
    # Whena -> When a
    # buyermay -> buyer may
    # notifythe -> notify the
    # bythe -> by the

    # Repair common PDF extraction word joins
    join_patterns = [
        (r"\bWhen(?=[a-z])", "When "),
        (r"\bwhen(?=[a-z])", "when "),
        (r"\bbuyer(?=[a-z])", "buyer "),
        (r"\bnotify(?=[a-z])", "notify "),
        (r"\bshould(?=[a-z])", "should "),
        (r"\bother(?=[a-z])", "other "),
        (r"\brelevant(?=[a-z])", "relevant "),
        (r"\bby(?=[a-z])", "by "),
        (r"\bof(?=[a-z])", "of "),
    ]

    for pattern, replacement in join_patterns:
        text = re.sub(pattern, replacement, text)

        # Join broken lines inside sentences
    text = re.sub(
        r"\n(?=[a-z])",
        " ",
        text,
    )

    # Normalize excessive blank lines
    text = re.sub(
        r"\n\s*\n\s*\n+",
        "\n\n",
        text,
    )

    return text.strip()


def split_text(
    text: str,
    chunk_size: int = 800,
    overlap: int = 150,
) -> list[str]:
    """Split text into overlapping chunks."""

    if chunk_size <= 0:
        raise ValueError(
            "chunk_size must be greater than zero"
        )

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError(
            "overlap must be >= 0 and < chunk_size"
        )

    chunks = []

    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size

        chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk.strip())

        if end >= text_length:
            break

        start = end - overlap

    return chunks


def extract_legal_metadata(text: str) -> dict:
    """Extract chapter and section metadata."""

    chapter = None
    section = None
    section_title = None

    chapter_match = re.search(
        r"(CHAPTER\s+[IVXLCDM]+\s*[-—:]\s*.+)",
        text,
        re.IGNORECASE,
    )

    if chapter_match:
        chapter = chapter_match.group(1).strip()

    section_match = re.search(
        r"(?im)^\s*(SECTION\s+\d+[A-Za-z]?)"
        r"(?=\s*[.\-—:]|\s+[A-Z]|$)",
        text,
    )

    if section_match:
        section = section_match.group(1).upper()

    else:
        article_match = re.search(
            r"(?im)^\s*(ARTICLE\s+\d+[A-Za-z]?)"
            r"(?=\s*[.\-—:]|\s+[A-Z]|$)",
            text,
        )

        if article_match:
            section = article_match.group(1).title()

        else:
            number_match = re.search(
                r"(?im)^\s*(\d+)[.\-:]\s+"
                r"((?:Compensation|Definitions|"
                r"Interpretation|Application|Liability|"
                r"Penalty|Offences|Exceptions|Remedies)"
                r"\b[^\n]{0,120})",
                text,
            )

            if number_match:
                number = number_match.group(1)

                section = f"SECTION {number}"

                section_title = (
                    number_match.group(2).strip()
                )

    return {
        "chapter": chapter,
        "section": section,
        "section_title": section_title,
    }


def split_at_legal_headings(text: str) -> list[str]:
    """
    Split text at legal headings.
    Keeps title/chapter text with first section.
    """

    heading_pattern = re.compile(
        r"(?im)^(?=(?:SECTION|ARTICLE)\s+\d+[A-Za-z]?\b)"
    )

    matches = list(
        heading_pattern.finditer(text)
    )

    if len(matches) < 2:
        return [text] if text.strip() else []

    blocks = []

    start = 0

    for match in matches[1:]:
        block = text[start:match.start()].strip()

        if block:
            blocks.append(block)

        start = match.start()

    final_block = text[start:].strip()

    if final_block:
        blocks.append(final_block)

    return blocks


def split_pages(
    pages: list[str],
    chunk_size: int = 800,
    overlap: int = 150,
) -> list[dict]:
    """
    Create chunks with page, chapter,
    and legal-section metadata.
    """

    page_chunks = []

    current_chapter = None
    current_section = None
    current_title = None

    for page_number, page_text in enumerate(
        pages,
        start=1,
    ):

        cleaned_page = clean_pdf_text(page_text)

        if not cleaned_page:
            continue

        legal_blocks = split_at_legal_headings(
            cleaned_page
        )

        for block in legal_blocks:

            chunks = split_text(
                block,
                chunk_size,
                overlap,
            )

            metadata = extract_legal_metadata(
                block
            )

            if metadata["chapter"]:
                current_chapter = metadata["chapter"]

            if metadata["section"]:
                current_section = metadata["section"]
                current_title = metadata[
                    "section_title"
                ]

            for chunk in chunks:

                chunk_metadata = (
                    extract_legal_metadata(chunk)
                )

                if chunk_metadata["chapter"]:
                    current_chapter = (
                        chunk_metadata["chapter"]
                    )

                if chunk_metadata["section"]:
                    current_section = (
                        chunk_metadata["section"]
                    )

                    current_title = (
                        chunk_metadata["section_title"]
                    )

                page_chunks.append(
                    {
                        "page_number": page_number,
                        "content": chunk,
                        "chapter": current_chapter,
                        "section": current_section,
                        "section_title": current_title,
                    }
                )

    return page_chunks