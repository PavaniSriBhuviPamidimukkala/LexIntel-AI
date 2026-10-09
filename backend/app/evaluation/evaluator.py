from app.evaluation.dataset import load_dataset
from app.evaluation.metrics import (
    hit_at_k,
    section_hit,
    precision_at_k,
    reciprocal_rank,
)
from app.retrieval.search import search_documents


def evaluate(db, limit=5, dataset=None):
    """
    Evaluate retrieval against the configured dataset.

    Pass dataset explicitly to test evaluation behavior without changing
    the configured JSON file.
    """
    if limit < 1:
        raise ValueError("limit must be at least 1")

    questions = load_dataset() if dataset is None else dataset

    if not questions:
        return {
            "total_questions": 0,
            "average_hit_at_k": 0.0,
            "average_section_hit": 0.0,
            "average_precision": 0.0,
            "average_mrr": 0.0,
            "details": [],
        }

    results_report = []
    total_hit = 0
    total_section_hit = 0
    total_precision = 0.0
    total_mrr = 0.0
    section_question_count = 0

    for item in questions:
        question = item["question"]
        expected_document = item["expected_document"]
        expected_section = item.get("expected_section")

        results = search_documents(question, db, limit=limit)

        hit = hit_at_k(results, expected_document)
        precision = precision_at_k(results, expected_document)
        mrr = reciprocal_rank(results, expected_document)

        section_score = None
        if expected_section:
            section_score = section_hit(results, expected_section)
            total_section_hit += section_score
            section_question_count += 1

        total_hit += hit
        total_precision += precision
        total_mrr += mrr

        results_report.append(
            {
                "question": question,
                "expected_document": expected_document,
                "expected_section": expected_section,
                "hit": hit,
                "section_hit": section_score,
                "precision": precision,
                "mrr": mrr,
            }
        )

    count = len(questions)

    return {
        "total_questions": count,
        "average_hit_at_k": total_hit / count,
        "average_section_hit": (
            total_section_hit / section_question_count
            if section_question_count
            else 0.0
        ),
        "average_precision": total_precision / count,
        "average_mrr": total_mrr / count,
        "details": results_report,
    }


if __name__ == "__main__":
    from app.database import SessionLocal
    from app.evaluation.report import format_report

    db = SessionLocal()
    try:
        report = evaluate(db)
        print(format_report(report))
    finally:
        db.close()
