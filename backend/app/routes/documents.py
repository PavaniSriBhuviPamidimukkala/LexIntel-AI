from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from pypdf import PdfReader
import os

from app.database import SessionLocal
from app.models.legal_document import LegalDocument
from app.schemas.document import DocumentCreate, DocumentResponse
from app.embeddings.generator import generate_embedding
from app.retrieval.search import search_documents


router = APIRouter(
    prefix="/documents",
    tags=["Documents"]
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=DocumentResponse)
def create_document(
    document: DocumentCreate,
    db: Session = Depends(get_db)
):
    db_document = LegalDocument(
        title=document.title,
        content=document.content,
        category=document.category
    )

    db.add(db_document)
    db.commit()
    db.refresh(db_document)

    return db_document


@router.get("/", response_model=list[DocumentResponse])
def get_documents(
    db: Session = Depends(get_db)
):
    documents = db.query(LegalDocument).all()
    return documents


@router.post("/upload", response_model=DocumentResponse)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    reader = PdfReader(file.file)

    text = ""

    for page in reader.pages:
        text += page.extract_text() or ""

    title = os.path.splitext(file.filename)[0]

    embedding = generate_embedding(text)

    document = LegalDocument(
        title=title,
        content=text,
        category="Uploaded PDF",
        embedding=embedding
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document


@router.get("/search")
def search_document(
    q: str,
    db: Session = Depends(get_db)
):
    results = search_documents(q, db)

    return [
        {
            "id": document.id,
            "title": document.title,
            "category": document.category,
            "content": document.content,
            "hybrid_score": float(distance)
        }
        for document, distance in results
    ]
