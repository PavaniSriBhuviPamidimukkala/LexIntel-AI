from app.evaluation.dataset import load_dataset, validate_dataset
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
from app.evaluation.performance import (
    PERFORMANCE_STAGES,
    capture_timings,
    summarize_samples,
    timed_stage,
    timing_snapshot,
)
from app.rag.pipeline import rag_pipeline


RETRIEVAL_METRICS = {
    "precision_at_k": precision_at_k,
    "recall_at_k": recall_at_k,
    "mrr": reciprocal_rank,
    "ndcg_at_k": ndcg_at_k,
}


def _metric_arguments(item, limit):
    return {
        "expected_document": item["expected_document"],
        "k": limit,
        "expected_section": item.get("expected_section"),
        "expected_chunk": item.get("expected_chunk"),
    }


def _empty_report(limit):
    metric_names = (
        "precision_at_k",
        "recall_at_k",
        "mrr",
        "ndcg_at_k",
        "citation_accuracy",
        "source_coverage",
        "unsupported_claim_count",
        "hallucination_rate",
    )
    return {
        "total_questions": 0,
        "k": limit,
        "average_hit_at_k": 0.0,
        "average_section_hit": 0.0,
        "average_precision": 0.0,
        "average_recall": 0.0,
        "average_mrr": 0.0,
        "average_ndcg": 0.0,
        "metrics": {name: 0.0 for name in metric_names},
        "performance": summarize_samples({}),
        "details": [],
    }


def evaluate(db, user_id: int, limit=5, dataset=None):
    """
    Evaluate retrieval and generated response quality against a benchmark.

    Each benchmark entry has one expected document and may narrow that target
    by page, section, or chunk. Expected evidence is optional and controls
    whether source coverage is included in the aggregate.
    """
    if limit < 1:
        raise ValueError("limit must be at least 1")

    questions = load_dataset() if dataset is None else dataset
    validate_dataset(questions)
    if not questions:
        return _empty_report(limit)

    metric_totals = {name: 0.0 for name in RETRIEVAL_METRICS}
    quality_totals = {
        "citation_accuracy": 0.0,
        "source_coverage": 0.0,
        "unsupported_claim_count": 0.0,
        "hallucination_rate": 0.0,
    }
    coverage_question_count = 0
    total_hit = 0
    total_section_hit = 0
    section_question_count = 0
    results_report = []
    question_performance_samples = {
        stage: [] for stage in PERFORMANCE_STAGES
    }
    upload_performance_samples = timing_snapshot()

    for item in questions:
        with capture_timings() as run_timings:
            with timed_stage("end_to_end_response_time"):
                response = rag_pipeline(
                    item["question"],
                    db,
                    user_id=user_id,
                    limit=limit,
                )

        for stage in PERFORMANCE_STAGES:
            question_performance_samples[stage].extend(
                run_timings.get(stage, [])
            )

        answer = response.get("answer") or ""
        citations = response.get("citations") or []
        metric_arguments = _metric_arguments(item, limit)
        question_metrics = {
            name: metric(citations, **metric_arguments)
            for name, metric in RETRIEVAL_METRICS.items()
        }

        document_hit = hit_at_k(citations, item["expected_document"])
        expected_section = item.get("expected_section")
        matched_section = (
            section_hit(citations, expected_section)
            if expected_section
            else None
        )

        response_metrics = {
            "citation_accuracy": citation_accuracy(citations, item),
            "source_coverage": source_coverage(
                citations,
                item.get("expected_evidence"),
            ),
            **unsupported_claims(answer, citations),
        }

        for name, value in question_metrics.items():
            metric_totals[name] += value
        for name, value in response_metrics.items():
            if value is not None and name in quality_totals:
                quality_totals[name] += value
        if response_metrics["source_coverage"] is not None:
            coverage_question_count += 1

        total_hit += document_hit
        if matched_section is not None:
            total_section_hit += matched_section
            section_question_count += 1

        results_report.append(
            {
                "question": item["question"],
                "expected_document": item["expected_document"],
                "expected_page": item.get("expected_page"),
                "expected_section": expected_section,
                "expected_chunk": item.get("expected_chunk"),
                "expected_evidence": item.get("expected_evidence"),
                "answer": answer,
                "retrieved_count": len(citations),
                "hit": document_hit,
                "section_hit": matched_section,
                **question_metrics,
                **response_metrics,
                "performance": summarize_samples(run_timings),
                # Keep this alias for compatibility with existing report users.
                "precision": question_metrics["precision_at_k"],
            }
        )

    count = len(questions)
    average_metrics = {
        name: total / count
        for name, total in metric_totals.items()
    }
    average_metrics["citation_accuracy"] = (
        quality_totals["citation_accuracy"] / count
    )
    average_metrics["source_coverage"] = (
        quality_totals["source_coverage"] / coverage_question_count
        if coverage_question_count
        else None
    )
    average_metrics["unsupported_claim_count"] = (
        quality_totals["unsupported_claim_count"] / count
    )
    average_metrics["hallucination_rate"] = (
        quality_totals["hallucination_rate"] / count
    )
    for stage in (
        "pdf_upload_time",
        "pdf_parsing_time",
        "chunking_time",
        "embedding_generation_time",
    ):
        question_performance_samples[stage].extend(
            upload_performance_samples.get(stage, [])
        )

    return {
        "total_questions": count,
        "k": limit,
        "average_hit_at_k": total_hit / count,
        "average_section_hit": (
            total_section_hit / section_question_count
            if section_question_count
            else 0.0
        ),
        "average_precision": average_metrics["precision_at_k"],
        "average_recall": average_metrics["recall_at_k"],
        "average_mrr": average_metrics["mrr"],
        "average_ndcg": average_metrics["ndcg_at_k"],
        "metrics": average_metrics,
        "performance": summarize_samples(question_performance_samples),
        "details": results_report,
    }


if __name__ == "__main__":
    import argparse

    from app.database import SessionLocal
    from app.evaluation.report import format_report, write_reports

    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", type=int, required=True)
    args = parser.parse_args()
    db = SessionLocal()
    try:
        report = evaluate(db, user_id=args.user_id)
        print(format_report(report))
        json_path, csv_path = write_reports(report)
        print(f"\nReports written to {json_path} and {csv_path}")
    finally:
        db.close()
