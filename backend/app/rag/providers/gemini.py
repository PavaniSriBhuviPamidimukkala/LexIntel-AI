import requests

from app.core.config import settings
from app.rag.providers.base import LLMProvider

from tenacity import retry, stop_after_attempt, wait_exponential

class GeminiProvider(LLMProvider):
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(
            multiplier=1,
            min=2,
            max=10
        )
    )

    def generate(self, prompt: str) -> str:

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.GEMINI_MODEL}:generateContent"
        )

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": settings.GEMINI_API_KEY
        }

        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": prompt
                        }
                    ]
                }
            ]
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code != 200:
            print("Gemini Error:")
            print(response.text)
            response.raise_for_status()

        data = response.json()

        return (
            data["candidates"][0]
            ["content"]
            ["parts"][0]
            ["text"]
        )