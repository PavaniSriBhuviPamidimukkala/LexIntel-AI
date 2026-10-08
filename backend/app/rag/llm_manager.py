from app.core.config import settings
from app.rag.providers.factory import get_provider


class LLMManager:

    def __init__(self):

        self.providers = [
            settings.LLM_PROVIDER,
            "ollama"
        ]

    def generate(self, prompt: str):

        last_exception = None

        used = set()

        for provider_name in self.providers:

            if provider_name in used:
                continue

            used.add(provider_name)

            try:

                print(f"Using provider: {provider_name}")

                provider = get_provider(provider_name)

                return provider.generate(prompt)

            except Exception as e:

                print(
                    f"{provider_name} failed:"
                    f" {e}"
                )

                last_exception = e

        raise last_exception