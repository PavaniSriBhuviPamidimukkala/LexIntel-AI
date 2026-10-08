from sqlalchemy.orm import Session

from app.retrieval.search import search_documents
from app.rag.context import build_context
from app.rag.prompts import build_prompt
from app.rag.generator import generate_answer

from app.citations.engine import generate_citations


def rag_pipeline(
    question: str,
    db: Session,
    limit: int = 5
):

    # 1. Retrieve relevant document chunks
    results = search_documents(
        question,
        db,
        limit
    )


    # 2. Build context from retrieved chunks
    context = build_context(
        results
    )


    # 3. Build legal RAG prompt
    prompt = build_prompt(
        question,
        context
    )


    # 4. Generate AI answer
    try:
        answer = generate_answer(
            prompt
        )

    except Exception:
        answer = (
            "AI generation is temporarily unavailable.\n\n"
            "Relevant legal information is provided through citations."
        )


    # 5. Generate legal citations
    citations = generate_citations(
        results
    )


    return {
        "answer": answer,
        "citations": citations
    }