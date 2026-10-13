import argparse
import sys

sys.path.append("backend")

from app.database import SessionLocal
from app.models.legal_document import LegalDocument
from app.embeddings.generator import generate_embedding


def generate_missing_embeddings(user_id):
    db = SessionLocal()

    try:
        documents = (
            db.query(LegalDocument)
            .filter(
                LegalDocument.user_id == user_id,
                LegalDocument.embedding.is_(None),
            )
            .all()
        )

        print(f"Found {len(documents)} documents without embeddings")

        for document in documents:
            print(f"Generating embedding for: {document.title}")
            document.embedding = generate_embedding(document.content)

        db.commit()
        print("Embedding generation completed successfully!")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", type=int, required=True)
    args = parser.parse_args()
    generate_missing_embeddings(args.user_id)
