import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.evaluation import performance
from app.routes import metrics


class FakeQuery:
    def __init__(self, value):
        self.value = value

    def scalar(self):
        return self.value


class FakeDatabase:
    def __init__(self, values=(4, 3, 18), fail=False):
        self.values = iter(values)
        self.fail = fail
        self.rollback_called = False

    def execute(self, _statement):
        if self.fail:
            raise SQLAlchemyError("database unavailable")

    def query(self, _expression):
        return FakeQuery(next(self.values))

    def rollback(self):
        self.rollback_called = True


def make_client(database):
    app = FastAPI()
    app.include_router(metrics.router)
    app.dependency_overrides[metrics.get_db] = lambda: database
    return TestClient(app)


class TestEvaluationMetrics(unittest.TestCase):
    def test_records_aggregate_query_counts_without_query_content(self):
        with (
            patch.object(performance, "_query_count", 0),
            patch.object(performance, "_retrieval_success_count", 0),
            patch.object(performance, "_similarity_total", 0.0),
            patch.object(performance, "_similarity_sample_count", 0),
        ):
            performance.record_query(True, [0.8, 0.9])
            performance.record_query(False)

            self.assertEqual(
                performance.query_snapshot(),
                {
                    "total_queries_asked": 2,
                    "retrieval_success_count": 1,
                    "average_similarity_score": 0.85,
                },
            )

    def test_metrics_endpoint_returns_live_counts_and_health(self):
        database = FakeDatabase()
        with (
            patch(
                "app.routes.metrics.query_snapshot",
                return_value={
                    "total_queries_asked": 7,
                    "retrieval_success_count": 5,
                    "average_similarity_score": 0.87,
                },
            ),
            patch(
                "app.routes.metrics.timing_snapshot",
                return_value={
                    "end_to_end_response_time": [1.0, 3.0],
                    "retrieval_latency": [0.2, 0.4],
                },
            ),
        ):
            response = make_client(database).get("/metrics/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total_uploaded_documents"], 4)
        self.assertEqual(response.json()["total_processed_documents"], 3)
        self.assertEqual(response.json()["total_chunks"], 18)
        self.assertEqual(response.json()["average_response_time_seconds"], 2.0)
        self.assertAlmostEqual(
            response.json()["average_retrieval_time_seconds"],
            0.3,
        )
        self.assertEqual(response.json()["api_status"], "healthy")
        self.assertEqual(response.json()["database_status"], "healthy")

    def test_metrics_endpoint_reports_database_outage_without_masking_api(self):
        database = FakeDatabase(fail=True)
        with (
            patch(
                "app.routes.metrics.query_snapshot",
                return_value={
                    "total_queries_asked": 0,
                    "retrieval_success_count": 0,
                    "average_similarity_score": None,
                },
            ),
            patch(
                "app.routes.metrics.timing_snapshot",
                return_value={
                    "end_to_end_response_time": [],
                    "retrieval_latency": [],
                },
            ),
            self.assertLogs("app.routes.metrics", level="ERROR"),
        ):
            response = make_client(database).get("/metrics/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["api_status"], "healthy")
        self.assertEqual(response.json()["database_status"], "unavailable")
        self.assertIsNone(response.json()["total_uploaded_documents"])
        self.assertTrue(database.rollback_called)


if __name__ == "__main__":
    unittest.main()
