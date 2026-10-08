from app.rag.llm_manager import LLMManager


def generate_answer(prompt: str) -> str:
    """
    Generates an answer using the configured LLM.
    """

    manager = LLMManager()

    return manager.generate(prompt)