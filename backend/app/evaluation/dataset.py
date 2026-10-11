import json
from pathlib import Path


DATASET_PATH = (
    Path(__file__).parent
    / "test_questions.json"
)


def load_dataset(dataset_path=DATASET_PATH):
    """
    Loads evaluation questions.

    Returns:
        [
            {
                "question": "...",
                "expected_document": "...",
                "expected_section": "...",  # Optional
                "expected_chunk": 123,       # Optional
            }
        ]
    """

    with open(dataset_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    validate_dataset(dataset)
    return dataset


def validate_dataset(dataset):
    """Validate benchmark entries before running retrieval."""
    if not isinstance(dataset, list):
        raise ValueError("Evaluation dataset must be a list of objects.")

    for index, item in enumerate(dataset):
        if not isinstance(item, dict):
            raise ValueError(
                f"Evaluation dataset entry {index + 1} must be an object."
            )

        for field in ("question", "expected_document"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise ValueError(
                    f"Evaluation dataset entry {index + 1} requires a "
                    f"non-empty '{field}'."
                )

        for field in ("expected_section", "expected_evidence"):
            value = item.get(field)
            if value is not None and not isinstance(value, str):
                raise ValueError(
                    f"Evaluation dataset entry {index + 1} has an invalid "
                    f"'{field}'."
                )

        for field in ("expected_page", "expected_chunk"):
            value = item.get(field)
            if value is not None and not isinstance(value, (str, int)):
                raise ValueError(
                    f"Evaluation dataset entry {index + 1} has an invalid "
                    f"'{field}'."
                )