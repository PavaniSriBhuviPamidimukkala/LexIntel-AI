from sqlalchemy.orm import Session

from app.retrieval.search import search_documents
from app.rag.context import build_context
from app.rag.prompts import build_prompt
from app.rag.generator import generate_answer


def rag_pipeline(
    question: str,
    db: Session,
    limit: int = 5
):

    # 1. Retrieve relevant documents
    results = search_documents(
        question,
        db,
        limit
    )


    # 2. Build context
    context = build_context(results)


    # 3. Create legal prompt
    prompt = build_prompt(
        question,
        context
    )


    # 4. Generate answer
    answer = generate_answer(
        prompt
    )

    return {
        "answer": answer,
        "sources": [
            {
                "title": document.title,
                "category": document.category,
                "score": round(float(score), 4)
            }
            for chunk, score in results
        ]
    }
