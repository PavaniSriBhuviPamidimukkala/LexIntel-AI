
from pathlib import Path

from pypdf import PdfReader

from app.database import SessionLocal
from app.models.legal_document import LegalDocument
from app.models.document_chunk import DocumentChunk
from app.utils.chunker import split_pages
from app.embeddings.generator import generate_embedding


DOCUMENT_ID = 24
PDF_PATH = Path("lexintel_test_upload.pdf")


def main():
    if not PDF_PATH.is_file():
        raise FileNotFoundError(f"PDF not found: {PDF_PATH}")

    reader = PdfReader(str(PDF_PATH))
    pages = [page.extract_text() or "" for page in reader.pages]
    full_text = "\n".join(pages)

    # Prepare and validate all replacement chunks before touching the DB.
    chunks = split_pages(pages)

    sections = {chunk["section"] for chunk in chunks}
    required_sections = {"SECTION 12", "SECTION 13"}

    if not required_sections.issubset(sections):
        raise ValueError(
            f"Expected sections {required_sections}; found {sections}"
        )

    prepared_chunks = []

    for item in chunks:
        content = item["content"]
        if not content.strip():
            continue

        chapter = item.get("chapter")
        section = item.get("section")
        section_title = item.get("section_title")

        # Match the existing upload route's act-name detection.
        act_name = next(
            (
                line.strip()
                for line in full_text.split("\n")[:15]
                if any(
                    term in line.upper()
                    for term in ("ACT", "REGULATION", "LAW")
                )
            ),
            "lexintel_test_upload",
        )

        metadata = {
            "act_name": act_name,
            "document_type": "Uploaded PDF",
            "page_number": item["page_number"],
            "chapter": chapter,
            "section": section,
            "section_title": section_title,
        }

        prepared_chunks.append(
            {
                "content": content,
                "page_number": item["page_number"],
                "section": section,
                "metadata_json": metadata,
                "embedding": generate_embedding(content),
            }
        )

    if not prepared_chunks:
        raise ValueError("No replacement chunks were prepared")

    db = SessionLocal()

    try:
        with db.begin():
            document = db.get(LegalDocument, DOCUMENT_ID)

            if document is None:
                raise ValueError(
                    f"Document ID {DOCUMENT_ID} does not exist"
                )

            if document.title != "lexintel_test_upload":
                raise ValueError(
                    f"Unexpected document title: {document.title!r}"
                )

            # Replace only this document's chunks.
            db.query(DocumentChunk).filter(
                DocumentChunk.document_id == DOCUMENT_ID
            ).delete(synchronize_session=False)

            for item in prepared_chunks:
                db.add(
                    DocumentChunk(
                        document_id=DOCUMENT_ID,
                        content=item["content"],
                        page_number=item["page_number"],
                        section=item["section"],
                        metadata_json=item["metadata_json"],
                        embedding=item["embedding"],
                    )
                )

        print(f"Document {DOCUMENT_ID} refreshed successfully.")
        print(f"New chunk count: {len(prepared_chunks)}")

        for item in prepared_chunks:
            print(
                f"Section: {item['section']} | "
                f"Page: {item['page_number']}"
            )

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()