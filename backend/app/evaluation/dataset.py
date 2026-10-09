import json
from pathlib import Path


DATASET_PATH = (
    Path(__file__).parent
    / "test_questions.json"
)


def load_dataset():
    """
    Loads evaluation questions.

    Returns:
        [
            {
                question,
                expected_document,
                expected_section
            }
        ]
    """

    with open(
        DATASET_PATH,
        "r",
        encoding="utf-8"
    ) as f:

        return json.load(f)