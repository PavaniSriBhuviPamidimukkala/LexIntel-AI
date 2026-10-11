import requests

from app.core.config import settings
from app.rag.providers.base import LLMProvider


class OllamaProvider(LLMProvider):

    def generate(self, prompt: str) -> str:

        response = requests.post(
            f"{settings.OLLAMA_BASE_URL.rstrip('/')}/api/generate",
            json={
                "model": settings.OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            },
            timeout=120
        )

        response.raise_for_status()

        return response.json()["response"]