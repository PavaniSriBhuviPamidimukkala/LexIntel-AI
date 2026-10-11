import csv
import json
import math
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from app.evaluation.dataset import validate_dataset
from app.evaluation.evaluator import evaluate
from app.evaluation.performance import (
    capture_timings,
    summarize_samples,
    timed_stage,
)
from app.evaluation.metrics import (
    hit_at_k,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
    section_hit,
)
from app.evaluation.quality_metrics import (
    citation_accuracy,
    source_coverage,
    unsupported_claims,
)
from app.evaluation.report import format_report, write_reports


def make_result(title, section=None, score=1.0, chunk_id=None):
    chunk = SimpleNamespace(
        document=SimpleNamespace(title=title),
        section=section,
        id=chunk_id,
    )
    return chunk, score


class TestEvaluationMetrics(unittest.TestCase):
    def test_hit_is_case_insensitive(self):
        results = [make_result("Indian Contract Act 1872")]
        self.assertEqual(hit_at_k(results, "indian contract act 1872"), 1)

    def test_precision_at_k_uses_k_as_denominator(self):
        results = [make_result("Expected Act"), make_result("Other Act")]
        self.assertEqual(
            precision_at_k(results, "Expected Act", k=5),
            0.2,
        )

    def test_precision_counts_each_relevant_result_in_top_k(self):
        results = [
            make_result("Indian Contract Act 1872"),
            make_result("Other Act"),
        ]
        self.assertEqual(
            precision_at_k(
                results,
                "Indian Contract Act 1872",
                k=2,
            ),
            0.5,
        )

    def test_recall_at_k_matches_all_supplied_labels(self):
        results = [
            make_result("Expected Act", "Section 8", chunk_id=1),
            make_result("Expected Act", "Section 9", chunk_id=2),
        ]
        self.assertEqual(
            recall_at_k(
                results,
                "Expected Act",
                k=2,
                expected_section="Section 9",
                expected_chunk=2,
            ),
            1.0,
        )
        self.assertEqual(
            recall_at_k(
                results,
                "Expected Act",
                k=1,
                expected_section="Section 9",
            ),
            0.0,
        )

    def test_reciprocal_rank_uses_first_relevant_position(self):
        results = [
            make_result("Other Act"),
            make_result("Indian Contract Act 1872"),
        ]
        self.assertEqual(
            reciprocal_rank(results, "Indian Contract Act 1872"),
            0.5,
        )

    def test_reciprocal_rank_respects_k(self):
        results = [
            make_result("Other Act"),
            make_result("Expected Act"),
        ]
        self.assertEqual(
            reciprocal_rank(results, "Expected Act", k=1),
            0.0,
        )

    def test_ndcg_rewards_relevant_results_at_higher_ranks(self):
        high_ranked = [
            make_result("Expected Act"),
            make_result("Other Act"),
        ]
        low_ranked = [
            make_result("Other Act"),
            make_result("Expected Act"),
        ]
        self.assertEqual(ndcg_at_k(high_ranked, "Expected Act", k=2), 1.0)
        self.assertAlmostEqual(
            ndcg_at_k(low_ranked, "Expected Act", k=2),
            1 / math.log2(3),
        )

    def test_ndcg_is_zero_without_relevant_results(self):
        results = [make_result("Other Act")]
        self.assertEqual(ndcg_at_k(results, "Expected Act", k=5), 0.0)

    def test_metrics_require_positive_k(self):
        with self.assertRaises(ValueError):
            precision_at_k([], "Expected Act", k=0)
        with self.assertRaises(ValueError):
            recall_at_k([], "Expected Act", k=0)
        with self.assertRaises(ValueError):
            ndcg_at_k([], "Expected Act", k=0)

    def test_section_8_does_not_match_section_80(self):
        results = [make_result("Some Act", "SECTION 80")]
        self.assertEqual(section_hit(results, "Section 8"), 0)

    def test_section_match_ignores_case(self):
        results = [make_result("Some Act", "SECTION 73")]
        self.assertEqual(section_hit(results, "Section 73"), 1)


class TestEvaluationRunner(unittest.TestCase):
    @patch("app.evaluation.evaluator.rag_pipeline")
    def test_empty_dataset_returns_zero_metrics(self, mock_search):
        result = evaluate(db=None, dataset=[])

        self.assertEqual(result["total_questions"], 0)
        self.assertEqual(result["average_hit_at_k"], 0.0)
        self.assertEqual(result["metrics"]["ndcg_at_k"], 0.0)
        self.assertIsNone(
            result["performance"]["retrieval_latency"]["average"]
        )
        self.assertEqual(result["details"], [])
        mock_search.assert_not_called()

    @patch("app.evaluation.evaluator.rag_pipeline")
    def test_evaluator_handles_optional_expected_labels(self, mock_search):
        mock_search.return_value = {
            "answer": "The law provides a remedy for breach of contract.",
            "citations": [
                {
                    "source": "Expected Act",
                    "page": 2,
                    "section": "Section 1",
                    "chunk_id": 4,
                    "quote": "A remedy is provided for breach of contract.",
                }
            ],
        }

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
        self.assertEqual(result["average_precision"], 0.2)
        self.assertEqual(result["average_recall"], 1.0)
        self.assertEqual(result["average_section_hit"], 0.0)
        self.assertIsNone(result["details"][0]["section_hit"])
        self.assertEqual(
            result["details"][0]["performance"][
                "end_to_end_response_time"
            ]["samples"],
            1,
        )
        mock_search.assert_called_once_with("Test question", None, limit=5)

    @patch("app.evaluation.evaluator.rag_pipeline")
    def test_evaluator_reports_all_metrics_with_expected_chunk(
        self,
        mock_search,
    ):
        mock_search.return_value = {
            "answer": "Expected evidence describes a legal remedy.",
            "citations": [
                {
                    "source": "Other Act",
                    "page": 3,
                    "section": "Section 2",
                    "chunk_id": 6,
                    "quote": "Other legal content.",
                },
                {
                    "source": "Expected Act",
                    "page": 7,
                    "section": "Section 2",
                    "chunk_id": 7,
                    "quote": "Expected evidence describes a legal remedy.",
                },
            ],
        }

        result = evaluate(
            db=None,
            dataset=[
                {
                    "question": "Test question",
                    "expected_document": "Expected Act",
                    "expected_section": "Section 2",
                    "expected_chunk": 7,
                    "expected_page": 7,
                    "expected_evidence": "Expected evidence describes a legal remedy.",
                }
            ],
        )

        detail = result["details"][0]
        self.assertEqual(detail["precision_at_k"], 0.2)
        self.assertEqual(detail["recall_at_k"], 1.0)
        self.assertEqual(detail["mrr"], 0.5)
        self.assertAlmostEqual(detail["ndcg_at_k"], 1 / math.log2(3))
        self.assertEqual(detail["citation_accuracy"], 0.5)
        self.assertEqual(detail["source_coverage"], 1.0)
        self.assertEqual(detail["unsupported_claim_count"], 0)
        self.assertEqual(detail["hallucination_rate"], 0.0)

    def test_dataset_validation_requires_question_and_document(self):
        with self.assertRaisesRegex(ValueError, "expected_document"):
            validate_dataset([{"question": "test"}])

    def test_dataset_validation_accepts_optional_labels(self):
        validate_dataset(
            [
                {
                    "question": "test",
                    "expected_document": "Expected Act",
                    "expected_chunk": 3,
                    "expected_page": 2,
                    "expected_evidence": "a supporting quote",
                }
            ]
        )

    def test_citation_accuracy_checks_document_page_section_and_chunk(self):
        citations = [
            {
                "source": "Expected Act",
                "page": 7,
                "section": "SECTION 73",
                "chunk_id": 9,
            },
            {
                "source": "Expected Act",
                "page": 8,
                "section": "SECTION 73",
                "chunk_id": 10,
            },
        ]
        benchmark = {
            "expected_document": "Expected Act",
            "expected_page": 7,
            "expected_section": "Section 73",
            "expected_chunk": 9,
        }
        self.assertEqual(citation_accuracy(citations, benchmark), 0.5)

    def test_source_coverage_measures_expected_evidence_tokens(self):
        citations = [
            {"quote": "The party receives compensation after breach."}
        ]
        self.assertEqual(
            source_coverage(
                citations,
                "party receives compensation following contract breach",
            ),
            4 / 6,
        )
        self.assertIsNone(source_coverage(citations, None))

    def test_unsupported_claims_counts_unsupported_sentences(self):
        answer = (
            "The party receives compensation after breach. "
            "Mars is made of blue cheese."
        )
        citations = [
            {"quote": "The party receives compensation after breach."}
        ]
        self.assertEqual(
            unsupported_claims(answer, citations),
            {
                "unsupported_claim_count": 1,
                "hallucination_rate": 0.5,
                "answer_sentence_count": 2,
            },
        )

    def test_report_includes_requested_console_metrics(self):
        report = format_report(
            {
                "total_questions": 0,
                "k": 5,
                "metrics": {
                    "precision_at_k": 0.0,
                    "recall_at_k": 0.0,
                    "mrr": 0.0,
                    "ndcg_at_k": 0.0,
                    "citation_accuracy": 0.0,
                    "source_coverage": 0.0,
                    "unsupported_claim_count": 0.0,
                    "hallucination_rate": 0.0,
                },
                "details": [],
            }
        )
        self.assertIn("Precision@5", report)
        self.assertIn("Recall@5", report)
        self.assertIn("MRR:", report)
        self.assertIn("nDCG@5", report)
        self.assertIn("Citation accuracy", report)
        self.assertIn("Source coverage", report)
        self.assertIn("Unsupported claims", report)
        self.assertIn("No evaluation questions were available.", report)

    def test_console_summary_includes_performance_distribution(self):
        report = format_report(
            {
                "total_questions": 1,
                "k": 5,
                "metrics": {},
                "performance": {
                    "retrieval_latency": {
                        "samples": 2,
                        "average": 0.2,
                        "median": 0.2,
                        "minimum": 0.1,
                        "maximum": 0.3,
                        "standard_deviation": 0.14,
                    }
                },
                "details": [],
            }
        )

        self.assertIn("avg=0.200", report)
        self.assertIn("median=0.200", report)
        self.assertIn("min=0.100", report)
        self.assertIn("max=0.300", report)
        self.assertIn("stddev=0.140", report)

    def test_report_writer_creates_json_and_csv(self):
        report = {
            "total_questions": 1,
            "k": 5,
            "metrics": {
                "precision_at_k": 0.2,
                "recall_at_k": 1.0,
                "mrr": 1.0,
                "ndcg_at_k": 1.0,
            },
            "performance": {
                "retrieval_latency": {
                    "samples": 3,
                    "average": 0.2,
                    "median": 0.18,
                    "minimum": 0.1,
                    "maximum": 0.32,
                    "standard_deviation": 0.11,
                }
            },
            "details": [
                {
                    "question": "Test question",
                    "expected_document": "Expected Act",
                    "expected_section": None,
                    "expected_chunk": None,
                    "retrieved_count": 5,
                    "hit": 1,
                    "section_hit": None,
                    "precision_at_k": 0.2,
                    "recall_at_k": 1.0,
                    "mrr": 1.0,
                    "ndcg_at_k": 1.0,
                    "citation_accuracy": 1.0,
                    "source_coverage": 0.8,
                    "unsupported_claim_count": 1,
                    "answer_sentence_count": 2,
                    "hallucination_rate": 0.5,
                    "performance": {
                        "retrieval_latency": {
                            "samples": 1,
                            "average": 0.2,
                            "median": 0.2,
                            "minimum": 0.2,
                            "maximum": 0.2,
                            "standard_deviation": None,
                        }
                    },
                }
            ],
        }

        with tempfile.TemporaryDirectory() as directory:
            json_path, csv_path = write_reports(report, directory)

            with json_path.open(encoding="utf-8") as report_file:
                self.assertEqual(
                    json.load(report_file)["metrics"]["mrr"],
                    1.0,
                )
            with csv_path.open(encoding="utf-8", newline="") as report_file:
                rows = list(csv.DictReader(report_file))

        self.assertEqual(
            [row["record_type"] for row in rows],
            ["summary", "question", "performance"],
        )
        self.assertEqual(rows[1]["expected_document"], "Expected Act")
        self.assertEqual(rows[1]["citation_accuracy"], "1.0")
        self.assertEqual(rows[1]["hallucination_rate"], "0.5")
        self.assertEqual(rows[2]["performance_stage"], "retrieval_latency")
        self.assertEqual(rows[2]["average_seconds"], "0.2")

    def test_performance_summary_reports_distribution(self):
        summary = summarize_samples(
            {
                "retrieval_latency": [1.0, 2.0, 3.0],
            }
        )["retrieval_latency"]

        self.assertEqual(summary["samples"], 3)
        self.assertEqual(summary["average"], 2.0)
        self.assertEqual(summary["median"], 2.0)
        self.assertEqual(summary["minimum"], 1.0)
        self.assertEqual(summary["maximum"], 3.0)
        self.assertEqual(summary["standard_deviation"], 1.0)

    def test_timed_stage_captures_run_measurement(self):
        with capture_timings() as timings:
            with timed_stage("retrieval_latency"):
                pass

        self.assertEqual(len(timings["retrieval_latency"]), 1)
        self.assertGreaterEqual(timings["retrieval_latency"][0], 0.0)


if __name__ == "__main__":
    unittest.main()
