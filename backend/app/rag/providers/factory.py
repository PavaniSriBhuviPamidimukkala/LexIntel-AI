from app.core.config import settings

from app.rag.providers.gemini import GeminiProvider
from app.rag.providers.ollama import OllamaProvider


def get_llm_provider():

    if settings.LLM_PROVIDER == "gemini":
        return GeminiProvider()

    elif settings.LLM_PROVIDER == "ollama":
        return OllamaProvider()

    else:
        raise ValueError(
            f"Unsupported LLM provider: {settings.LLM_PROVIDER}"
        )