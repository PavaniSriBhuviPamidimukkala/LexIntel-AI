import argparse

from app.database import SessionLocal
from app.retrieval.search import search_documents


def test_search(user_id):

    db = SessionLocal()

    query = "What happens in breach of contract?"

    results = search_documents(
        query,
        db,
        user_id=user_id,
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
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", type=int, required=True)
    args = parser.parse_args()
    test_search(args.user_id)