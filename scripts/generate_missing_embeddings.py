import sys

sys.path.append("backend")

from app.database import SessionLocal
from app.models.legal_document import LegalDocument
from app.embeddings.generator import generate_embedding


db = SessionLocal()

documents = (
    db.query(LegalDocument)
    .filter(LegalDocument.embedding.is_(None))
    .all()
)

print(f"Found {len(documents)} documents without embeddings")


for document in documents:
    print(f"Generating embedding for: {document.title}")

    vector = generate_embedding(document.content)

    document.embedding = vector


db.commit()

print("Embedding generation completed successfully!")

db.close()
