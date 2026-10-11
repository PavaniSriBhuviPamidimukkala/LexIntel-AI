import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.retrieval.search import (
    get_requested_section,
    get_requested_reference,
    chunk_matches_section,
    chunk_matches_reference,
    search_documents,
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

    def test_extracts_article_reference(self):
        self.assertEqual(
            get_requested_reference("What does Article 16 DSA require?"),
            ("article", "16"),
        )

    def test_section_73_contract_act_retrieval_filters_before_vectors(self):
        exact_chunk = self.make_chunk(
            73,
            "Indian Contract Act 1872",
            "SECTION 73",
            act_name="Indian Contract Act, 1872",
        )
        wrong_document = self.make_chunk(
            730,
            "Digital Markets Act",
            "SECTION 73",
            act_name="Digital Markets Act",
        )
        wrong_section = self.make_chunk(
            89,
            "Indian Contract Act 1872",
            "SECTION 89",
            act_name="Indian Contract Act, 1872",
        )

        results, candidate_ids = self.run_search(
            "What does Section 73 of the Contract Act say?",
            [wrong_document, wrong_section, exact_chunk],
        )

        self.assertEqual(candidate_ids, [73])
        self.assertEqual([chunk.id for chunk, _ in results], [73])

    def test_section_89_retrieval_filters_to_exact_section(self):
        exact_chunk = self.make_chunk(89, "Section 89 Overview", "SECTION 89")
        other_chunk = self.make_chunk(8, "Section 89 Overview", "SECTION 8")

        results, candidate_ids = self.run_search(
            "What is Section 89 relief?",
            [other_chunk, exact_chunk],
        )

        self.assertEqual(candidate_ids, [89])
        self.assertEqual([chunk.id for chunk, _ in results], [89])

    def test_article_16_dsa_retrieval_matches_title_acronym(self):
        exact_chunk = self.make_chunk(
            16,
            "Digital Services Act (EU 2022/2065)",
            "Article 16",
            act_name="Digital Services Act",
        )
        wrong_article = self.make_chunk(
            6,
            "Digital Services Act (EU 2022/2065)",
            "Article 6",
            act_name="Digital Services Act",
        )
        wrong_document = self.make_chunk(
            116,
            "Digital Markets Act",
            "Article 16",
            act_name="Digital Markets Act",
        )

        results, candidate_ids = self.run_search(
            "What does Article 16 DSA require?",
            [wrong_article, wrong_document, exact_chunk],
        )

        self.assertEqual(candidate_ids, [16])
        self.assertEqual([chunk.id for chunk, _ in results], [16])

    @staticmethod
    def make_chunk(chunk_id, title, section, act_name=None):
        return SimpleNamespace(
            id=chunk_id,
            document_id=chunk_id,
            section=section,
            content=(
                f"{section} provides legal rights and obligations. "
                "The applicable act establishes rules and remedies "
                "for a person affected by these legal provisions."
            ),
            metadata_json={"act_name": act_name} if act_name else {},
            document=SimpleNamespace(title=title),
        )

    @staticmethod
    def run_search(query, chunks):
        db = SimpleNamespace(
            query=lambda _model: SimpleNamespace(
                all=lambda: chunks
            )
        )
        searched_candidate_ids = []

        def semantic_search(_query, _db, candidate_ids=None):
            searched_candidate_ids[:] = candidate_ids or []
            return {chunk_id: 0.9 for chunk_id in searched_candidate_ids}

        with (
            patch(
                "app.retrieval.search.semantic_search",
                side_effect=semantic_search,
            ),
            patch(
                "app.retrieval.search.keyword_search",
                side_effect=lambda _query, candidate_chunks: {
                    chunk.id: 0.0 for chunk in candidate_chunks
                },
            ),
        ):
            results = search_documents(query, db, limit=5)

        return results, searched_candidate_ids

    def test_exact_section_query_keeps_matching_section_ahead_of_other_sections(self):
        exact_chunk = SimpleNamespace(
            id=73,
            document_id=1,
            section="SECTION 73",
            content=(
                "Compensation for breach of contract and related legal "
                "remedies under this section."
            ),
            document=SimpleNamespace(title="Contract Act"),
        )
        other_chunk = SimpleNamespace(
            id=89,
            document_id=2,
            section="SECTION 89",
            content=(
                "General provisions and legal rules that are unrelated "
                "to the requested compensation section."
            ),
            document=SimpleNamespace(title="Contract Act"),
        )
        db = SimpleNamespace(
            query=lambda _model: SimpleNamespace(
                all=lambda: [other_chunk, exact_chunk]
            )
        )

        with (
            patch(
                "app.retrieval.search.semantic_search",
                return_value={73: 0.8, 89: 1.0},
            ),
            patch(
                "app.retrieval.search.keyword_search",
                return_value={73: 0.0, 89: 0.0},
            ),
        ):
            results = search_documents(
                "Explain Section 73 compensation",
                db,
                limit=2,
            )

        self.assertEqual([chunk.id for chunk, _ in results], [73])


if __name__ == "__main__":
    unittest.main()
