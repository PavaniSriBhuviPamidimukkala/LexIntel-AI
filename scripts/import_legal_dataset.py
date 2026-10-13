import argparse

from datasets import load_dataset

from app.database import SessionLocal
from app.models.legal_document import LegalDocument
from app.models.user import User
from app.embeddings.generator import generate_embedding


def import_documents(user_id):

    db = SessionLocal()

    try:
        if db.get(User, user_id) is None:
            raise ValueError(f"User {user_id} does not exist")

        dataset = load_dataset(
            "dedol-hf/india-case-legal-rag",
            split="train"
        )

        print(f"Loaded {len(dataset)} legal documents")

        for index, item in enumerate(dataset):

            content = item["text"]

            source = item["metadata"]["source"]


            embedding = generate_embedding(content)


            document = LegalDocument(
                user_id=user_id,
                title=source,
                content=content,
                category="Supreme Court Judgment",
                embedding=embedding
            )


            db.add(document)


            if index % 100 == 0:
                db.commit()
                print(f"Imported {index} documents")

        db.commit()
        print("Import completed successfully")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--user-id", type=int, required=True)
    args = parser.parse_args()
    import_documents(args.user_id)