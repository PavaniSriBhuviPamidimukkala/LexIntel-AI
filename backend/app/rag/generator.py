from app.rag.providers.factory import get_llm_provider


def generate_answer(prompt: str):

    provider = get_llm_provider()

    return provider.generate(prompt)