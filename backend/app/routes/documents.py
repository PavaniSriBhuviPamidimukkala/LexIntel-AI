from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session

from pypdf import PdfReader
from pypdf.errors import PdfReadError

import os
import re


from app.auth import get_current_user
from app.database import get_db
from app.core.config import settings

from app.models.legal_document import LegalDocument
from app.models.document_chunk import DocumentChunk


from app.schemas.document import (
    DocumentCreate,
    DocumentResponse
)

from app.schemas.search import SearchResult


from app.embeddings.generator import generate_embedding

from app.retrieval.search import search_documents

from app.utils.chunker import split_pages
from app.evaluation.performance import timed_function, timed_stage



router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
    redirect_slashes=False,
    dependencies=[Depends(get_current_user)],
)


def validate_pdf_upload(file: UploadFile) -> None:
    filename = file.filename or ""
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF documents can be uploaded.",
        )

    file.file.seek(0, os.SEEK_END)
    file_size = file.file.tell()
    file.file.seek(0)

    if file_size == 0:
        raise HTTPException(
            status_code=400,
            detail="The uploaded PDF is empty.",
        )

    if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=(
                "The PDF exceeds the maximum upload size of "
                f"{settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB."
            ),
        )

    if b"%PDF-" not in file.file.read(1024):
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is not a valid PDF.",
        )
    file.file.seek(0)



# ==================================================
# ACT NAME DETECTION
# ==================================================

def extract_act_name(title, text):

    lines = text.split("\n")


    for line in lines[:15]:

        clean = line.strip()


        if (
            "ACT" in clean.upper()
            or "REGULATION" in clean.upper()
            or "LAW" in clean.upper()
        ):

            return clean


    return title





# ==================================================
# CHAPTER DETECTION
# ==================================================

def extract_chapter(text):

    pattern = r"(CHAPTER\s+[IVXLCDM0-9]+\s*[—-]?\s*[A-Z &]+)"


    match = re.search(
        pattern,
        text,
        re.IGNORECASE
    )


    if match:

        return match.group(1).strip()


    return None





# ==================================================
# SECTION / ARTICLE DETECTION
# ==================================================

def extract_section(text):

    patterns = [
        r"(SECTION\s+\d+[A-Za-z]?)"
        r"(?=\s*[.\-—:]\s*|\s+(?-i:[A-Z])|\s*$)",

        r"(ARTICLE\s+\d+[A-Za-z]?)"
        r"(?=\.\s+(?-i:[A-Z]))",

        r"(Sec\.\s*\d+)"
        r"(?=\s*[.\-—:]|\s*$)"
    ]


    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )


        if match:

            value = match.group(1).strip()


            if value.lower().startswith("section"):

                return value.upper()


            if value.lower().startswith("article"):

                number = re.search(
                    r"\d+[A-Za-z]?",
                    value
                )

                if number:

                    return (
                        f"Article {number.group()}"
                    )


            return value


    return None





# ==================================================
# SECTION TITLE DETECTION
# ==================================================

def extract_section_title(text):

    lines=text.split("\n")


    for line in lines:


        line=line.strip()


        if not line:

            continue



        if (
            "—" in line
            or ".—" in line
            or ")-" in line
        ):


            parts=re.split(
                r"—|\.—|\)-",
                line
            )


            if len(parts)>1:


                title=parts[-1].strip()


                if len(title)>3:

                    return title



    return None






# ==================================================
# CREATE DOCUMENT
# ==================================================

@router.post(
    "/",
    response_model=DocumentResponse
)
def create_document(

    document:DocumentCreate,

    db:Session=Depends(get_db)

):


    db_document=LegalDocument(

        title=document.title,

        content=document.content,

        category=document.category

    )


    db.add(db_document)

    db.commit()

    db.refresh(db_document)


    return db_document






# ==================================================
# GET DOCUMENTS
# ==================================================

@router.get(
    "",
    response_model=list[DocumentResponse]
)
def get_documents(

    db:Session=Depends(get_db)

):

    return (

        db.query(LegalDocument)
        .all()

    )







# ==================================================
# UPLOAD PDF
# ==================================================

@router.post(
    "/upload",
    response_model=DocumentResponse
)
@timed_function("pdf_upload_time")
def upload_document(

    file:UploadFile=File(...),

    db:Session=Depends(get_db)

):

    filename = file.filename or ""
    validate_pdf_upload(file)

    with timed_stage("pdf_parsing_time"):
        try:
            reader = PdfReader(file.file)
            if reader.is_encrypted:
                raise HTTPException(
                    status_code=400,
                    detail="Encrypted PDFs are not supported.",
                )
            title = os.path.splitext(filename)[0]
            pages = [
                page.extract_text() or ""
                for page in reader.pages
            ]
        except (PdfReadError, ValueError) as exc:
            raise HTTPException(
                status_code=400,
                detail="The uploaded PDF could not be read.",
            ) from exc





    full_text="\n".join(pages)



    act_name=extract_act_name(
        title,
        full_text
    )



    with timed_stage("chunking_time"):
        page_chunks = split_pages(pages)



    chunks=[]



    current_chapter=None

    current_section=None

    current_title=None





    with timed_stage("embedding_generation_time"):
        for item in page_chunks:


            content = item["content"]


            if not content.strip():

                continue


            chapter = item.get("chapter")
            if chapter:
                current_chapter = chapter

            section = item.get("section")
            if section:
                current_section = section
                current_title = item.get("section_title")

            embedding = generate_embedding(content)


            metadata = {
                "act_name": act_name,
                "document_type": "Uploaded PDF",
                "page_number": item["page_number"],
                "chapter": current_chapter,
                "section": current_section,
                "section_title": current_title,
            }

            chunk = DocumentChunk(
                content=content,
                page_number=item["page_number"],
                section=current_section,
                metadata_json=metadata,
                embedding=embedding,
            )
            chunks.append(chunk)







    document=LegalDocument(

        title=title,


        content=full_text,


        category="Uploaded PDF"

    )



    db.add(document)

    db.commit()

    db.refresh(document)







    for chunk in chunks:


        chunk.document_id=document.id

        db.add(chunk)



    db.commit()

    db.refresh(document)



    return document







# ==================================================
# SEARCH
# ==================================================

@router.get(
    "/search",
    response_model=list[SearchResult]
)
def search_document(

    q:str,

    db:Session=Depends(get_db)

):


    results=search_documents(
        q,
        db
    )


    return [

        {

            "id":chunk.id,


            "title":
                chunk.document.title,


            "category":
                chunk.document.category,


            "snippet":
                chunk.content[:500],


            "score":
                float(score)

        }


        for chunk,score in results

    ]