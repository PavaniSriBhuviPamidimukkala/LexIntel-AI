from datasets import load_dataset

from app.database import SessionLocal
from app.models.legal_document import LegalDocument
from app.embeddings.generator import generate_embedding


def import_documents():

    db = SessionLocal()

    dataset = load_dataset(
        "dedol-hf/india-case-legal-rag",
        split="train"
    )

    print(f"Loaded {len(dataset)} legal documents")


    for index, item in enumerate(dataset):

        content = item["text"]

        source = item["metadata"]["source"]


        # Generate vector embedding
        embedding = generate_embedding(content)


        document = LegalDocument(
            title=source,
            content=content,
            category="Supreme Court Judgment",
            embedding=embedding
        )


        db.add(document)


        # Save in batches
        if index % 100 == 0:
            db.commit()
            print(f"Imported {index} documents")


    db.commit()

    db.close()

    print("Import completed successfully")


if __name__ == "__main__":
    import_documents()