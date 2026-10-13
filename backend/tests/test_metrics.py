import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.evaluation import performance
from app.auth import require_current_user
from app.models.chat_history import ChatHistory
from app.routes import metrics


class FakeQuery:
    def __init__(self, value):
        self.value = value
        self.filters = []

    def filter(self, *criteria):
        self.filters.extend(criteria)
        return self

    def join(self, *_args, **_kwargs):
        return self

    def order_by(self, *_args, **_kwargs):
        return self

    def scalar(self):
        return self.value

    def all(self):
        return self.value


class FakeDatabase:
    def __init__(self, values=(4, 3, 18), history=(), fail=False):
        self.values = iter(values)
        self.history = list(history)
        self.fail = fail
        self.rollback_called = False
        self.queries = []

    def execute(self, _statement):
        if self.fail:
            raise SQLAlchemyError("database unavailable")

    def query(self, expression):
        value = self.history if expression is ChatHistory else next(self.values)
        query = FakeQuery(value)
        self.queries.append(query)
        return query

    def rollback(self):
        self.rollback_called = True


def make_client(database):
    app = FastAPI()
    app.include_router(metrics.router)
    app.dependency_overrides[metrics.get_db] = lambda: database
    app.dependency_overrides[require_current_user] = (
        lambda: SimpleNamespace(id=7)
    )
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
        database = FakeDatabase(
            history=[
                SimpleNamespace(
                    response_time_seconds=1.0,
                    retrieval_time_seconds=0.2,
                    retrieval_succeeded=True,
                    average_similarity_score=0.8,
                ),
                SimpleNamespace(
                    response_time_seconds=3.0,
                    retrieval_time_seconds=0.4,
                    retrieval_succeeded=False,
                    average_similarity_score=None,
                ),
            ]
        )
        response = make_client(database).get("/metrics/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["total_uploaded_documents"], 4)
        self.assertEqual(response.json()["total_processed_documents"], 3)
        self.assertEqual(response.json()["total_chunks"], 18)
        self.assertEqual(response.json()["total_queries_asked"], 2)
        self.assertEqual(response.json()["retrieval_success_count"], 1)
        self.assertEqual(response.json()["average_similarity_score"], 0.8)
        self.assertEqual(response.json()["response_time_history"], [1.0, 3.0])
        self.assertEqual(response.json()["retrieval_time_history"], [0.2, 0.4])
        self.assertEqual(response.json()["average_response_time_seconds"], 2.0)
        self.assertAlmostEqual(
            response.json()["average_retrieval_time_seconds"],
            0.3,
        )
        self.assertEqual(response.json()["api_status"], "healthy")
        self.assertEqual(response.json()["database_status"], "healthy")
        for query in database.queries:
            for predicate in query.filters:
                self.assertEqual(predicate.right.value, 7)

    def test_metrics_endpoint_reports_database_outage_without_masking_api(self):
        database = FakeDatabase(fail=True)
        with self.assertLogs("app.routes.metrics", level="ERROR"):
            response = make_client(database).get("/metrics/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["api_status"], "healthy")
        self.assertEqual(response.json()["database_status"], "unavailable")
        self.assertIsNone(response.json()["total_uploaded_documents"])
        self.assertTrue(database.rollback_called)


if __name__ == "__main__":
    unittest.main()
