
import unittest
from types import SimpleNamespace

from app.rag.pipeline import build_fallback_answer


LEGAL_PASSAGE = (
    "Section 73 of the Indian Contract Act, 1872 provides that when a "
    "contract is broken, the injured party is entitled to compensation "
    "for loss or damage that naturally arose in the usual course of "
    "things from the breach of contract."
)


def make_chunk(content, title="Test Legal Act", page=1):
    document = SimpleNamespace(title=title)
    return SimpleNamespace(
        content=content,
        document=document,
        page_number=page,
    )


class TestRAGFallback(unittest.TestCase):

    def test_empty_results(self):
        answer = build_fallback_answer([])
        self.assertIn("no relevant document passages", answer.lower())

    def test_source_and_excerpt_included(self):
        chunk = make_chunk(LEGAL_PASSAGE)
        answer = build_fallback_answer([chunk])

        self.assertIn("Test Legal Act", answer)
        self.assertIn("Section 73", answer)
        self.assertIn("page 1", answer)

    def test_duplicate_excerpts_removed(self):
        chunk = make_chunk(LEGAL_PASSAGE)
        answer = build_fallback_answer([chunk, chunk])

        self.assertEqual(answer.count("Relevant excerpt:"), 1)

    def test_maximum_three_excerpts(self):
        chunks = [
            make_chunk(
                LEGAL_PASSAGE + f" Additional legal explanation number {i}.",
                page=i,
            )
            for i in range(1, 6)
        ]
        answer = build_fallback_answer(chunks)

        self.assertEqual(answer.count("Relevant excerpt:"), 3)

    def test_boilerplate_is_filtered(self):
        boilerplate = make_chunk(
            "Statutory Sample • The Indian Contract Act, 1872. "
            + LEGAL_PASSAGE
        )
        answer = build_fallback_answer([boilerplate])

        self.assertNotIn("Statutory Sample", answer)

    def test_low_relevance_result_is_filtered(self):
        chunk = make_chunk(LEGAL_PASSAGE)
        answer = build_fallback_answer([(chunk, 0.10)])

        self.assertNotIn("Relevant excerpt:", answer)

    def test_relevant_scored_result_is_included(self):
        chunk = make_chunk(LEGAL_PASSAGE)
        answer = build_fallback_answer([(chunk, 0.50)])

        self.assertIn("Relevant excerpt:", answer)
        self.assertIn("Section 73", answer)

    def test_long_excerpt_does_not_exceed_limit_or_split_word(self):
        content = (
            "Section 73 provides compensation for breach of contract. "
            * 100
        )
        chunk = make_chunk(content)
        answer = build_fallback_answer([chunk])

        excerpt = answer.split("Relevant excerpt: ", 1)[1]

        self.assertLessEqual(len(excerpt), 903)
        self.assertTrue(
            excerpt.endswith(".") or excerpt.endswith("...")
        )


if __name__ == "__main__":
    unittest.main()

