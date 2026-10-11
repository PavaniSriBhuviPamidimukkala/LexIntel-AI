import csv
import json
from pathlib import Path


def _aggregate_metric(report, metric_name, legacy_name):
    metrics = report.get("metrics", {})
    if metric_name in metrics:
        return metrics[metric_name]
    return report.get(legacy_name, 0.0)


def _format_seconds(value):
    return f"{value:.3f}" if value is not None else "N/A"


def format_report(report):
    """Format aggregate retrieval metrics and per-question results."""
    total = report.get("total_questions", 0)
    k = report.get("k", 5)
    precision = _aggregate_metric(
        report,
        "precision_at_k",
        "average_precision",
    )
    recall = _aggregate_metric(
        report,
        "recall_at_k",
        "average_recall",
    )
    mrr = _aggregate_metric(report, "mrr", "average_mrr")
    ndcg = _aggregate_metric(report, "ndcg_at_k", "average_ndcg")
    metrics = report.get("metrics", {})
    citation_accuracy = metrics.get("citation_accuracy", 0.0)
    source_coverage = metrics.get("source_coverage")
    unsupported_claim_count = metrics.get("unsupported_claim_count", 0.0)
    hallucination_rate = metrics.get("hallucination_rate", 0.0)
    performance = report.get("performance", {})

    lines = [
        "LexIntel AI Retrieval Evaluation",
        "=" * 34,
        f"Questions evaluated: {total}",
        f"Precision@{k}: {precision:.3f}",
        f"Recall@{k}:    {recall:.3f}",
        f"MRR:           {mrr:.3f}",
        f"nDCG@{k}:       {ndcg:.3f}",
        f"Citation accuracy: {citation_accuracy:.3f}",
        "Source coverage:   "
        + (f"{source_coverage:.3f}" if source_coverage is not None else "N/A"),
        f"Unsupported claims: {unsupported_claim_count:.2f} per answer",
        f"Hallucination rate: {hallucination_rate:.3f}",
        "",
        "Performance (seconds)",
    ]
    for stage, summary in performance.items():
        lines.append(
            f"{stage}: avg={_format_seconds(summary.get('average'))} "
            f"median={_format_seconds(summary.get('median'))} "
            f"min={_format_seconds(summary.get('minimum'))} "
            f"max={_format_seconds(summary.get('maximum'))} "
            f"stddev={_format_seconds(summary.get('standard_deviation'))} "
            f"n={summary.get('samples', 0)}"
        )

    details = report.get("details", [])
    if not details:
        lines.extend(["", "No evaluation questions were available."])
        return "\n".join(lines)

    lines.extend(["", "Question details", "-" * 34])
    for index, item in enumerate(details, start=1):
        lines.extend(
            [
                f"{index}. {item['question']}",
                f"   Expected document: {item['expected_document']}",
                f"   Expected section: {item.get('expected_section') or '—'}",
                f"   Expected chunk: {item.get('expected_chunk') or '—'}",
                f"   Precision@{k}: {item.get('precision_at_k', item.get('precision', 0.0)):.3f}",
                f"   Recall@{k}: {item.get('recall_at_k', 0.0):.3f}",
                f"   MRR: {item.get('mrr', 0.0):.3f}",
                f"   nDCG@{k}: {item.get('ndcg_at_k', 0.0):.3f}",
                f"   Citation accuracy: {item.get('citation_accuracy', 0.0):.3f}",
                "   Source coverage: "
                + (
                    f"{item['source_coverage']:.3f}"
                    if item.get("source_coverage") is not None
                    else "N/A"
                ),
                f"   Unsupported claims: {item.get('unsupported_claim_count', 0)}"
                f"/{item.get('answer_sentence_count', 0)} sentences",
                f"   Hallucination rate: {item.get('hallucination_rate', 0.0):.3f}",
                *[
                    f"   {stage}: "
                    + (
                        f"{summary['average']:.3f}s"
                        if summary.get("average") is not None
                        else "N/A"
                    )
                    for stage, summary in item.get("performance", {}).items()
                ],
            ]
        )

    lines.extend(
        [
            "",
            "Metrics use the supplied document/section/chunk labels as binary relevance.",
        ]
    )
    return "\n".join(lines)


def write_reports(report, output_dir="."):
    """Write aggregate and question-level results as JSON and CSV."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    json_path = output_path / "evaluation_report.json"
    csv_path = output_path / "evaluation_report.csv"

    with json_path.open("w", encoding="utf-8") as report_file:
        json.dump(report, report_file, indent=2, ensure_ascii=False)
        report_file.write("\n")

    fields = [
        "record_type",
        "total_questions",
        "question",
        "expected_document",
        "expected_page",
        "expected_section",
        "expected_chunk",
        "expected_evidence",
        "retrieved_count",
        "hit",
        "section_hit",
        "precision_at_k",
        "recall_at_k",
        "mrr",
        "ndcg_at_k",
        "citation_accuracy",
        "source_coverage",
        "unsupported_claim_count",
        "answer_sentence_count",
        "hallucination_rate",
        "performance_stage",
        "performance_samples",
        "average_seconds",
        "median_seconds",
        "minimum_seconds",
        "maximum_seconds",
        "standard_deviation_seconds",
    ]
    metrics = report.get("metrics", {})
    summary_row = {
        "record_type": "summary",
        "total_questions": report.get("total_questions", 0),
        "precision_at_k": metrics.get(
            "precision_at_k",
            report.get("average_precision", 0.0),
        ),
        "recall_at_k": metrics.get(
            "recall_at_k",
            report.get("average_recall", 0.0),
        ),
        "mrr": metrics.get("mrr", report.get("average_mrr", 0.0)),
        "ndcg_at_k": metrics.get(
            "ndcg_at_k",
            report.get("average_ndcg", 0.0),
        ),
        "citation_accuracy": metrics.get("citation_accuracy", 0.0),
        "source_coverage": metrics.get("source_coverage"),
        "unsupported_claim_count": metrics.get(
            "unsupported_claim_count",
            0.0,
        ),
        "hallucination_rate": metrics.get("hallucination_rate", 0.0),
    }

    with csv_path.open("w", encoding="utf-8", newline="") as report_file:
        writer = csv.DictWriter(report_file, fieldnames=fields)
        writer.writeheader()
        writer.writerow(summary_row)
        for detail in report.get("details", []):
            question_row = {
                field: detail.get(field)
                for field in fields
            }
            question_row["record_type"] = "question"
            writer.writerow(question_row)
        for stage, summary in report.get("performance", {}).items():
            writer.writerow(
                {
                    "record_type": "performance",
                    "performance_stage": stage,
                    "performance_samples": summary.get("samples", 0),
                    "average_seconds": summary.get("average"),
                    "median_seconds": summary.get("median"),
                    "minimum_seconds": summary.get("minimum"),
                    "maximum_seconds": summary.get("maximum"),
                    "standard_deviation_seconds": summary.get(
                        "standard_deviation"
                    ),
                }
            )

    return json_path, csv_path
