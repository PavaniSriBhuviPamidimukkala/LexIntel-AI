import logging
import requests

from app.core.config import settings
from app.rag.providers.base import LLMProvider

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    def generate(self, prompt: str) -> str:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.GEMINI_MODEL}:generateContent"
        )

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": settings.GEMINI_API_KEY or "",
        }

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "maxOutputTokens": 1024,
                "temperature": 0.2,
            },
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=45,
        )

        if response.status_code == 429:
            raise RuntimeError(
                "Gemini quota or rate limit reached. "
                "Check your Google AI Studio usage and quota."
            )

        if response.status_code == 404:
            raise RuntimeError(
                f"Gemini model '{settings.GEMINI_MODEL}' was not found "
                "or is unavailable for this API."
            )

        if response.status_code in (401, 403):
            raise RuntimeError(
                "Gemini authentication or permission failed. "
                "Check the API key and project settings."
            )

        response.raise_for_status()
        data = response.json()

        candidates = data.get("candidates", [])
        if not candidates:
            raise RuntimeError(
                "Gemini returned no answer candidates."
            )

        parts = candidates[0].get("content", {}).get("parts", [])
        answer = "\n".join(
            part["text"]
            for part in parts
            if "text" in part
        ).strip()

        if not answer:
            raise RuntimeError("Gemini returned an empty answer.")

        return answer
