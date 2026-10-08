from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from pypdf import PdfReader
import os

from app.database import SessionLocal
from app.models.legal_document import LegalDocument
from app.schemas.document import DocumentCreate, DocumentResponse
from app.schemas.search import SearchResult
from app.embeddings.generator import generate_embedding
from app.retrieval.search import search_documents
from app.models.document_chunk import DocumentChunk
from app.utils.chunker import split_text

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

    full_text = ""

    for page in reader.pages:
        full_text += page.extract_text() or ""


    title = os.path.splitext(file.filename)[0]


    # Store main document
    document = LegalDocument(
        title=title,
        content=full_text,
        category="Uploaded PDF"
    )

    db.add(document)
    db.commit()
    db.refresh(document)


    # Create chunks
    chunks = split_text(full_text)


    for index, chunk in enumerate(chunks):

        embedding = generate_embedding(chunk)

        document_chunk = DocumentChunk(
            document_id=document.id,
            content=chunk,
            page_number=index + 1,
            embedding=embedding
        )

        db.add(document_chunk)


    db.commit()


    return document


@router.get(
    "/search",
    response_model=list[SearchResult]
)
def search_document(
    q: str,
    db: Session = Depends(get_db)
):
    results = search_documents(q, db)

    return [
        {
            "id": chunk.id,
            "title": chunk.document.title,
            "category": chunk.document.category,
            "snippet": chunk.content[:500],
            "score": float(score)
        }
        for chunk, score in results
    ]
