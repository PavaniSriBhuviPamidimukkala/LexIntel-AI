import unittest

from app.citations.formatter import (
    format_all_citations,
    format_answer_with_citations,
    format_citation,
)


class TestCitationFormatter(unittest.TestCase):
    def test_formats_only_available_citation_fields(self):
        citation = {
            "source": "Contract Act",
            "page": 12,
            "section": "SECTION 73",
            "quote": "Compensation for loss caused by breach.",
            "chunk_id": 73,
            "relevance": 0.9,
        }

        self.assertEqual(
            format_citation(citation),
            "Contract Act — Section: SECTION 73 — Page: 12",
        )

    def test_missing_citation_fields_do_not_render_null_values(self):
        citation = {
            "source": "Privacy Act",
            "page": None,
            "section": "",
            "quote": None,
        }

        formatted = format_citation(citation)
        answer = format_answer_with_citations(
            "Legal Answer:\nEvidence is limited.",
            [citation],
        )

        self.assertEqual(formatted, "Privacy Act")
        self.assertNotIn("None", answer)
        self.assertNotIn("Page:", answer)
        self.assertNotIn("Section:", answer)
        self.assertIn("No retrieved evidence snippets are available.", answer)

    def test_multiple_sources_and_evidence_keep_input_order(self):
        citations = [
            {
                "source": "Contract Act",
                "page": 12,
                "section": "SECTION 73",
                "quote": "Damages may be recovered for breach.",
            },
            {
                "source": "Consumer Act",
                "page": 4,
                "section": "SECTION 5",
                "quote": "A consumer may seek redress.",
            },
        ]

        formatted = format_all_citations(citations)
        answer = format_answer_with_citations(
            "Legal Answer:\nSee [Source 1] and [Source 2].",
            citations,
        )

        self.assertEqual(
            formatted,
            [
                "Source 1: Contract Act — Section: SECTION 73 — Page: 12",
                "Source 2: Consumer Act — Section: SECTION 5 — Page: 4",
            ],
        )
        self.assertLess(answer.index("Source 1:"), answer.index("Source 2:"))
        self.assertIn("Damages may be recovered for breach.", answer)
        self.assertIn("A consumer may seek redress.", answer)

    def test_model_generated_source_and_evidence_sections_are_replaced(self):
        citations = [
            {
                "source": "Retrieved Act",
                "page": 6,
                "section": "SECTION 2",
                "quote": "Retrieved evidence only.",
            }
        ]

        answer = format_answer_with_citations(
            "Legal Answer:\nSupported answer [Source 1].\n\n"
            "Sources:\n- Invented Act, page 99\n\n"
            "Evidence:\n- Invented quotation.",
            citations,
        )

        self.assertNotIn("Invented Act", answer)
        self.assertNotIn("Invented quotation", answer)
        self.assertIn("Retrieved Act", answer)
        self.assertIn("Retrieved evidence only.", answer)

    def test_empty_citations_have_explicit_missing_citation_messages(self):
        answer = format_answer_with_citations("A general answer.", [])

        self.assertIn("Sources:\n- No citations are available", answer)
        self.assertIn(
            "Evidence:\n- No retrieved evidence snippets are available.",
            answer,
        )


if __name__ == "__main__":
    unittest.main()
