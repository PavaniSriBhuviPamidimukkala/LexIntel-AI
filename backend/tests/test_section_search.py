import unittest
from types import SimpleNamespace

from app.retrieval.search import (
    get_requested_section,
    chunk_matches_section,
)


class TestSectionSearch(unittest.TestCase):
    def test_extracts_section_73(self):
        self.assertEqual(
            get_requested_section("What is Section 73 of the Contract Act?"),
            "73",
        )

    def test_does_not_match_section_8_to_section_89(self):
        chunk = SimpleNamespace(
            section="SECTION 8",
            content="Section 8 " + "legal text " * 15,
        )
        self.assertFalse(chunk_matches_section(chunk, "89"))

    def test_matches_exact_section_metadata(self):
        chunk = SimpleNamespace(
            section="SECTION 73",
            content="Contract text " * 15,
        )
        self.assertTrue(chunk_matches_section(chunk, "73"))

    def test_matches_exact_section_in_content(self):
        chunk = SimpleNamespace(
            section=None,
            content="Section 73. Compensation for breach. " + "legal text " * 15,
        )
        self.assertTrue(chunk_matches_section(chunk, "73"))

    def test_does_not_extract_section_from_unrelated_number(self):
        self.assertIsNone(get_requested_section("Explain contract law generally."))


if __name__ == "__main__":
    unittest.main()
