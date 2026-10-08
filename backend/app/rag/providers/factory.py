from app.core.config import settings

from app.rag.providers.gemini import GeminiProvider
from app.rag.providers.ollama import OllamaProvider


PROVIDERS = {
    "gemini": GeminiProvider,
    "ollama": OllamaProvider,
}


def get_provider(provider_name: str):
    """
    Returns an LLM provider instance.
    """

    provider = PROVIDERS.get(provider_name.lower())

    if provider is None:
        raise ValueError(
            f"Unsupported LLM provider: {provider_name}"
        )

    return provider()


def get_llm_provider():
    """
    Returns the configured default provider.
    """

    return get_provider(settings.LLM_PROVIDER)