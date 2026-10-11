import logging

from app.core.config import settings
from app.rag.providers.factory import get_provider

logger = logging.getLogger(__name__)


class LLMManager:

    def __init__(self):
        self.provider_name = settings.LLM_PROVIDER

    def generate(self, prompt: str):
        logger.info(
            "Generating response with configured LLM provider %s",
            self.provider_name,
        )

        provider = get_provider(self.provider_name)
        try:
            return provider.generate(prompt)
        except Exception:
            logger.exception(
                "Configured LLM provider %s failed",
                self.provider_name,
            )
            raise