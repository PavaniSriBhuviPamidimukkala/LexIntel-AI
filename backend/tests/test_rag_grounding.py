import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.rag.context import build_context
from app.rag.pipeline import rag_pipeline
from app.rag.prompts import build_prompt


LEGAL_PASSAGE = (
    "Section 73 of the Contract Act provides compensation for loss or "
    "damage caused by a breach of contract. The injured party may recover "
    "losses that naturally arise in the usual course of events."
)


def make_result():
    document = SimpleNamespace(
        title="Contract Act",
        category="Legislation",
    )
    chunk = SimpleNamespace(
        id=73,
        content=LEGAL_PASSAGE,
        document=document,
        page_number=12,
        section="SECTION 73",
    )
    return chunk, 0.9


class TestRAGGrounding(unittest.TestCase):
    def test_prompt_requires_evidence_grounding_and_answer_structure(self):
        prompt = build_prompt(
            "What compensation is available?",
            "Source 1\nDocument:\nContract Act\nPage:\n12\n"
            "Section:\nSECTION 73\nContent:\n" + LEGAL_PASSAGE,
        )

        self.assertIn("using only the legal evidence", prompt)
        self.assertIn("Do not use external legal knowledge", prompt)
        self.assertIn(
            "The requested information is not available in the uploaded documents.",
            prompt,
        )
        for heading in (
            "Legal Answer:",
            "Explanation:",
            "Key Legal Points:",
            "Sources:",
        ):
            self.assertIn(heading, prompt)
        self.assertIn("Never invent or infer legal sections", prompt)

    def test_context_includes_available_source_metadata(self):
        context = build_context([make_result()])

        self.assertIn("Document:\nContract Act", context)
        self.assertIn("Page:\n12", context)
        self.assertIn("Section:\nSECTION 73", context)
        self.assertIn(LEGAL_PASSAGE, context)

    def test_pipeline_generates_grounded_answer_and_preserves_citations(self):
        expected_answer = (
            "Legal Answer:\nCompensation is available for supported losses "
            "[Source 1].\n\nExplanation:\nThe passage addresses breach "
            "damages.\n\nKey Legal Points:\n- Losses must naturally arise "
            "[Source 1]."
        )
        citations = [
            {
                "source": "Contract Act",
                "category": "Legislation",
                "page": 12,
                "section": "SECTION 73",
                "chapter": None,
                "chunk_id": 73,
                "quote": LEGAL_PASSAGE,
                "relevance": 0.9,
            }
        ]
        prompt_seen = []

        def generate(prompt):
            prompt_seen.append(prompt)
            return expected_answer

        with (
            patch("app.rag.pipeline.search_documents", return_value=[make_result()]),
            patch(
                "app.rag.pipeline.generate_citations",
                return_value=citations,
            ),
            patch("app.rag.pipeline.generate_answer", side_effect=generate),
        ):
            response = rag_pipeline("What compensation is available?", None)

        self.assertTrue(response["answer"].startswith(expected_answer))
        self.assertIn(
            "- Source 1: Contract Act — Section: SECTION 73 — Page: 12",
            response["answer"],
        )
        self.assertIn(f"  {LEGAL_PASSAGE}", response["answer"])
        self.assertIs(response["citations"], citations)
        self.assertIn(LEGAL_PASSAGE, prompt_seen[0])
        self.assertIn("SECTION 73", prompt_seen[0])

    def test_missing_evidence_returns_unavailable_message_without_generation(self):
        with (
            patch("app.rag.pipeline.search_documents", return_value=[]),
            patch("app.rag.pipeline.generate_answer") as generate,
        ):
            response = rag_pipeline("What does the uploaded document say?", None)

        self.assertEqual(
            response["answer"],
            "The requested information is not available in the uploaded documents.",
        )
        self.assertEqual(response["citations"], [])
        generate.assert_not_called()


if __name__ == "__main__":
    unittest.main()
