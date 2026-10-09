def format_report(report):
    """Format evaluation metrics and question-level results as plain text."""
    total = report.get("total_questions", 0)

    lines = [
        "LexIntel-AI Retrieval Evaluation",
        "=" * 32,
        f"Questions evaluated: {total}",
        f"Hit@K:               {report.get('average_hit_at_k', 0):.2%}",
        f"Section hit rate:    {report.get('average_section_hit', 0):.2%}",
        f"Precision@K:         {report.get('average_precision', 0):.2%}",
        f"Mean Reciprocal Rank:{report.get('average_mrr', 0): .3f}",
        "",
        "Question details",
        "-" * 32,
    ]

    details = report.get("details", [])
    if not details:
        lines.append("No evaluation questions were available.")
        return "\n".join(lines)

    for index, item in enumerate(details, start=1):
        lines.extend(
            [
                f"{index}. {item['question']}",
                f"   Expected document: {item['expected_document']}",
                f"   Document hit: {item['hit']}",
                f"   Section hit: {item['section_hit']}",
                f"   Precision: {item['precision']:.2f}",
                f"   Reciprocal rank: {item['mrr']:.2f}",
            ]
        )

    lines.extend(
        [
            "",
            "Note: these metrics evaluate retrieval labels, not legal correctness.",
        ]
    )
    return "\n".join(lines)
