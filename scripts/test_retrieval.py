from app.database import SessionLocal
from app.retrieval.search import search_documents


def test_search():

    db = SessionLocal()

    query = "What happens in breach of contract?"

    results = search_documents(
        query,
        db,
        limit=5
    )

    print("\nQUERY:")
    print(query)

    print("\nTOP RESULTS:\n")

    for document, score in results:

        print("=" * 60)
        print("TITLE:", document.title)
        print("CATEGORY:", document.category)
        print("SCORE:", score)
        print(
            document.content[:300]
        )


    db.close()


if __name__ == "__main__":
    test_search()