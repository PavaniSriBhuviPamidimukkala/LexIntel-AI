
import unittest

from app.utils.chunker import extract_legal_metadata, split_pages


class TestLegalMetadata(unittest.TestCase):

    def test_article_heading_is_detected(self):
        text = (
            "Article 16. Noticeand action mechanisms.— "
            "Providers shall establish a process for notices."
        )
        metadata = extract_legal_metadata(text)

        self.assertEqual(metadata["section"], "Article 16")

    def test_article_reference_is_not_mistaken_for_heading(self):
        text = (
            "Notices under thisArticle shall give rise to "
            "actual knowledge for the purposes of Article 6."
        )
        metadata = extract_legal_metadata(text)

        self.assertIsNone(metadata["section"])

    def test_continuation_chunk_keeps_previous_article(self):
        pages = [
            "Article 16. Noticeand action mechanisms. "
            + ("Notice procedures. " * 60)
        ]

        chunks = split_pages(pages, chunk_size=200, overlap=30)

        self.assertTrue(chunks)
        self.assertEqual(chunks[0]["section"], "Article 16")
        self.assertTrue(
            all(chunk["section"] == "Article 16" for chunk in chunks)
        )

    def test_section_reference_is_not_mistaken_for_heading(self):
        text = (
            "The obligations described in Section 8 apply "
            "to the data fiduciary."
        )
        metadata = extract_legal_metadata(text)

        self.assertIsNone(metadata["section"])

    def test_ordinary_numbered_list_is_not_mistaken_for_section(self):
        text = (
            "1. First step is to submit the form.\n"
            "2. Second step is to wait for review."
        )
        metadata = extract_legal_metadata(text)

        self.assertIsNone(metadata["section"])

    def test_numbered_legal_heading_with_period_is_detected(self):
        text = (
            "73. Compensation for loss or damage caused by breach "
            "of contract. When a contract has been broken, "
            "the party who suffers is entitled to compensation."
        )
        metadata = extract_legal_metadata(text)

        self.assertEqual(metadata["section"], "Section 73")

    def test_consecutive_sections_get_separate_chunks(self):
        pages = [
            "Section 12. Compensation for delayed delivery.\n"
            + ("The buyer may document direct losses. " * 5)
            + "\nSection 13. Notice of delay.\n"
            + ("A party should notify the other party promptly. " * 5)
        ]

        chunks = split_pages(pages, chunk_size=800, overlap=150)

        section_12_chunks = [
            chunk for chunk in chunks
            if chunk["section"] == "SECTION 12"
        ]
        section_13_chunks = [
            chunk for chunk in chunks
            if chunk["section"] == "SECTION 13"
        ]

        self.assertTrue(
            section_12_chunks,
            "Expected at least one chunk tagged SECTION 12",
        )
        self.assertTrue(
            section_13_chunks,
            "Expected at least one chunk tagged SECTION 13",
        )


if __name__ == "__main__":
    unittest.main()