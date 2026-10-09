import unittest
from types import SimpleNamespace

from app.retrieval.hybrid import hybrid_rank


def make_chunk(chunk_id, document_id, title, section=None, content=""):
    return SimpleNamespace(
        id=chunk_id,
        document_id=document_id,
        section=section,
        content=content,
        document=SimpleNamespace(title=title),
    )


class TestHybridRank(unittest.TestCase):
    def test_section_8_does_not_match_query_for_section_89(self):
        chunk = make_chunk(1, 1, "Data Protection Act", "SECTION 8")

        results = hybrid_rank(
            [chunk],
            {1: 0.8},
            {1: 0.0},
            "What is Section 89 relief?",
        )

        # Semantic contribution only: 0.45 * 0.8.
        self.assertAlmostEqual(results[0][1], 0.36)

    def test_exact_section_reference_gets_boost(self):
        chunk = make_chunk(1, 1, "Contract Act", "SECTION 89")

        results = hybrid_rank(
            [chunk],
            {1: 0.8},
            {1: 0.0},
            "What is Section 89 relief?",
        )

        self.assertAlmostEqual(results[0][1], 0.51)

    def test_repeated_chunks_are_limited_per_document(self):
        chunks = [
            make_chunk(1, 10, "First Act"),
            make_chunk(2, 10, "First Act"),
            make_chunk(3, 10, "First Act"),
            make_chunk(4, 20, "Second Act"),
        ]
        scores = {1: 0.9, 2: 0.8, 3: 0.7, 4: 0.6}

        results = hybrid_rank(
            chunks,
            scores,
            {},
            "Explain the rule",
            limit=3,
            max_per_document=2,
        )

        self.assertEqual(len(results), 3)
        self.assertEqual(
            sum(chunk.document_id == 10 for chunk, _ in results), 2
        )

    def test_topic_relevant_article_outranks_generic_notice_chunk(self):
        article_6 = make_chunk(
            1, 10, "Digital Services Act", "ARTICLE 6",
            "A notice may be submitted to the service provider.",
        )
        article_16 = make_chunk(
            2, 10, "Digital Services Act", "ARTICLE 16",
            "Notice and action mechanism for reporting illegal content.",
        )

        results = hybrid_rank(
            [article_6, article_16],
            {1: 0.6, 2: 0.55},
            {1: 0.3, 2: 0.3},
            "What is Notice and Action Mechanism?",
            max_per_document=2,
        )

        self.assertEqual(results[0][0].section, "ARTICLE 16")
    def test_topic_relevance_can_outweigh_small_semantic_advantage(self):
        unrelated = make_chunk(
            1, 10, "General Law",
            content="General legal provisions and miscellaneous rules.",
        )
        relevant = make_chunk(
            2, 20, "Digital Services Act",
            section="ARTICLE 16",
            content="Notice and action mechanism for reporting illegal content.",
        )

        results = hybrid_rank(
            [unrelated, relevant],
            {1: 0.70, 2: 0.60},
            {1: 0.0, 2: 0.30},
            "What is Notice and Action Mechanism?",
            max_per_document=2,
        )

        self.assertEqual(results[0][0].id, 2)

    def test_nonpositive_limit_returns_empty_results(self):
        chunk = make_chunk(1, 1, "Contract Act")

        self.assertEqual(
            hybrid_rank([chunk], {1: 1.0}, {}, "contract", limit=0),
            [],
        )


if __name__ == "__main__":
    unittest.main()
