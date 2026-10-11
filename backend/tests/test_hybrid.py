import unittest
from types import SimpleNamespace

from app.citations.engine import generate_citations
from app.retrieval.hybrid import hybrid_rank


def make_chunk(chunk_id, document_id, title, section=None, content=""):
    return SimpleNamespace(
        id=chunk_id,
        document_id=document_id,
        page_number=None,
        section=section,
        content=content,
        metadata_json={},
        document=SimpleNamespace(title=title, category=None),
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
            make_chunk(1, 10, "First Act", content="First passage."),
            make_chunk(2, 10, "First Act", content="Second passage."),
            make_chunk(3, 10, "First Act", content="Third passage."),
            make_chunk(4, 20, "Second Act", content="Fourth passage."),
        ]
        scores = {1: 0.9, 2: 0.8, 3: 0.7, 4: 0.7}

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

    def test_duplicate_content_keeps_highest_scoring_chunk(self):
        lower_scoring_copy = make_chunk(
            1, 10, "First Act", content="  Identical   legal content. "
        )
        higher_scoring_copy = make_chunk(
            2, 20, "Second Act", content="Identical legal content."
        )
        unique_chunk = make_chunk(
            3, 30, "Third Act", content="A different legal passage."
        )

        results = hybrid_rank(
            [lower_scoring_copy, higher_scoring_copy, unique_chunk],
            {1: 0.8, 2: 0.9, 3: 0.85},
            {},
            "Explain the rule",
            limit=2,
        )

        self.assertEqual(
            [chunk.id for chunk, _ in results],
            [2, 3],
        )
        citations = generate_citations(results)
        self.assertEqual(
            [citation["quote"] for citation in citations],
            ["Identical legal content.", "A different legal passage."],
        )

    def test_duplicate_content_does_not_consume_limit(self):
        chunks = [
            make_chunk(1, 10, "First Act", content="Repeated passage."),
            make_chunk(2, 20, "Second Act", content="Repeated   passage."),
            make_chunk(3, 30, "Third Act", content="Unique passage two."),
            make_chunk(4, 40, "Fourth Act", content="Unique passage three."),
        ]

        results = hybrid_rank(
            chunks,
            {1: 0.95, 2: 0.9, 3: 0.85, 4: 0.8},
            {},
            "Explain the rule",
            limit=3,
        )

        self.assertEqual(
            [chunk.id for chunk, _ in results],
            [1, 3, 4],
        )

    def test_prefers_different_sections_within_similar_score_range(self):
        chunks = [
            make_chunk(
                1, 10, "Contract Act", "SECTION 10",
                "alpha bravo charlie delta echo foxtrot golf hotel india",
            ),
            make_chunk(
                2, 10, "Contract Act", "SECTION 10",
                "juliet kilo lima mike november oscar papa quebec romeo",
            ),
            make_chunk(
                3, 10, "Contract Act", "SECTION 11",
                "sierra tango uniform victor whiskey xray yankee zulu alpha",
            ),
        ]

        results = hybrid_rank(
            chunks,
            {1: 0.95, 2: 0.93, 3: 0.88},
            {},
            "Explain the rule",
            limit=2,
            max_per_document=3,
        )

        self.assertEqual([chunk.id for chunk, _ in results], [1, 3])
        self.assertEqual(
            {chunk.section for chunk, _ in results},
            {"SECTION 10", "SECTION 11"},
        )

    def test_skips_substantially_overlapping_chunks(self):
        chunks = [
            make_chunk(
                1, 10, "Contract Act", "SECTION 10",
                "alpha bravo charlie delta echo foxtrot golf hotel india juliet",
            ),
            make_chunk(
                2, 20, "Contract Act", "SECTION 11",
                "alpha bravo charlie delta echo foxtrot golf hotel kilo lima",
            ),
            make_chunk(
                3, 30, "Contract Act", "SECTION 12",
                "november oscar papa quebec romeo sierra tango uniform victor",
            ),
        ]

        results = hybrid_rank(
            chunks,
            {1: 0.95, 2: 0.9, 3: 0.85},
            {},
            "Explain the rule",
            limit=2,
        )

        self.assertEqual([chunk.id for chunk, _ in results], [1, 3])

    def test_document_cap_does_not_allow_lower_scoring_duplicate(self):
        chunks = [
            make_chunk(1, 10, "First Act", content="First unique passage."),
            make_chunk(2, 10, "First Act", content="Repeated passage."),
            make_chunk(3, 20, "Second Act", content="Repeated passage."),
            make_chunk(4, 30, "Third Act", content="Another unique passage."),
        ]

        results = hybrid_rank(
            chunks,
            {1: 0.95, 2: 0.9, 3: 0.85, 4: 0.8},
            {},
            "Explain the rule",
            limit=3,
            max_per_document=1,
        )

        self.assertEqual(
            [chunk.id for chunk, _ in results],
            [1, 4],
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
