import unittest
from unittest.mock import Mock, patch

from app.rag.llm_manager import LLMManager
from app.rag.providers.factory import get_provider
from app.rag.providers.gemini import GeminiProvider


class TestLLMManager(unittest.TestCase):
    def test_factory_selects_configured_gemini_provider(self):
        with patch("app.rag.providers.factory.settings.LLM_PROVIDER", "gemini"):
            provider = get_provider("gemini")

        self.assertIsInstance(provider, GeminiProvider)

    def test_manager_uses_only_configured_provider(self):
        gemini = Mock()
        gemini.generate.return_value = "Gemini answer"

        with (
            patch("app.rag.llm_manager.settings.LLM_PROVIDER", "gemini"),
            patch(
                "app.rag.llm_manager.get_provider",
                return_value=gemini,
            ) as provider_factory,
        ):
            answer = LLMManager().generate("Question")

        self.assertEqual(answer, "Gemini answer")
        provider_factory.assert_called_once_with("gemini")
        gemini.generate.assert_called_once_with("Question")

    def test_configured_provider_failure_does_not_try_ollama(self):
        gemini = Mock()
        gemini.generate.side_effect = RuntimeError("Gemini request failed")

        with (
            patch("app.rag.llm_manager.settings.LLM_PROVIDER", "gemini"),
            patch(
                "app.rag.llm_manager.get_provider",
                return_value=gemini,
            ) as provider_factory,
            self.assertRaisesRegex(RuntimeError, "Gemini request failed"),
            self.assertLogs("app.rag.llm_manager", level="ERROR"),
        ):
            LLMManager().generate("Question")

        provider_factory.assert_called_once_with("gemini")
        gemini.generate.assert_called_once_with("Question")


if __name__ == "__main__":
    unittest.main()
