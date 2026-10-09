import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.evaluation.evaluator import evaluate
from app.evaluation.metrics import (
    hit_at_k,
    section_hit,
    precision_at_k,
    reciprocal_rank,
)
from app.evaluation.report import format_report


def make_result(title, section=None, score=1.0):
    chunk = SimpleNamespace(
        document=SimpleNamespace(title=title),
        section=section,
    )
    return chunk, score


class TestEvaluationMetrics(unittest.TestCase):
    def test_hit_is_case_insensitive(self):
        results = [make_result("Indian Contract Act 1872")]
        self.assertEqual(hit_at_k(results, "indian contract act 1872"), 1)

    def test_precision_counts_matching_documents(self):
        results = [
            make_result("Indian Contract Act 1872"),
            make_result("Other Act"),
        ]
        self.assertEqual(
            precision_at_k(results, "Indian Contract Act 1872"), 0.5
        )

    def test_reciprocal_rank_uses_first_matching_position(self):
        results = [
            make_result("Other Act"),
            make_result("Indian Contract Act 1872"),
        ]
        self.assertEqual(
            reciprocal_rank(results, "Indian Contract Act 1872"), 0.5
        )

    def test_section_8_does_not_match_section_80(self):
        results = [make_result("Some Act", "SECTION 80")]
        self.assertEqual(section_hit(results, "Section 8"), 0)

    def test_section_match_ignores_case(self):
        results = [make_result("Some Act", "SECTION 73")]
        self.assertEqual(section_hit(results, "Section 73"), 1)

    @patch("app.evaluation.evaluator.search_documents")
    def test_empty_dataset_returns_zero_metrics(self, mock_search):
        result = evaluate(db=None, dataset=[])

        self.assertEqual(result["total_questions"], 0)
        self.assertEqual(result["average_hit_at_k"], 0.0)
        self.assertEqual(result["details"], [])
        mock_search.assert_not_called()

    @patch("app.evaluation.evaluator.search_documents")
    def test_evaluator_handles_questions_without_expected_section(
        self, mock_search
    ):
        mock_search.return_value = [make_result("Expected Act", "Section 1")]

        result = evaluate(
            db=None,
            dataset=[
                {
                    "question": "Test question",
                    "expected_document": "Expected Act",
                }
            ],
        )

        self.assertEqual(result["total_questions"], 1)
        self.assertEqual(result["average_hit_at_k"], 1.0)
        self.assertEqual(result["average_section_hit"], 0.0)
        self.assertIsNone(result["details"][0]["section_hit"])

    def test_report_handles_empty_dataset(self):
        report = format_report(
            {
                "total_questions": 0,
                "average_hit_at_k": 0.0,
                "average_section_hit": 0.0,
                "average_precision": 0.0,
                "average_mrr": 0.0,
                "details": [],
            }
        )
        self.assertIn("No evaluation questions were available.", report)


if __name__ == "__main__":
    unittest.main()
