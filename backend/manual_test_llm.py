from app.rag.generator import generate_answer


prompt = """
You are LexIntel AI.

Explain Section 73 of the Indian Contract Act briefly.
"""


response = generate_answer(prompt)

print(response)
