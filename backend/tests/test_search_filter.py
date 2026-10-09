import unittest
from types import SimpleNamespace

from app.retrieval.search import is_retrievable_chunk


class TestRetrievableChunk(unittest.TestCase):
    def test_rejects_statutory_sample_placeholder(self):
        chunk = SimpleNamespace(
            content="Statutory Sample • The Indian Contract Act, 1872"
        )
        self.assertFalse(is_retrievable_chunk(chunk))

    def test_rejects_very_short_chunk(self):
        chunk = SimpleNamespace(content="Section 73")
        self.assertFalse(is_retrievable_chunk(chunk))

    def test_accepts_substantive_legal_text(self):
        chunk = SimpleNamespace(
            content=(
                "Section 73. Compensation for loss or damage caused "
                "by breach of contract. When a contract has been broken, "
                "the party who suffers by such breach is entitled to "
                "receive compensation for any loss or damage caused."
            )
        )
        self.assertTrue(is_retrievable_chunk(chunk))

    def test_rejects_placeholder_case_insensitively(self):
        chunk = SimpleNamespace(
            content=(
                "STATUTORY SAMPLE " + "placeholder text " * 10
            )
        )
        self.assertFalse(is_retrievable_chunk(chunk))


if __name__ == "__main__":
    unittest.main()
