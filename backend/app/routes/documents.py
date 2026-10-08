from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session

from pypdf import PdfReader

import os
import re


from app.database import SessionLocal

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

        r"(Section\s+\d+[A-Za-z]?)",

        r"(SECTION\s+\d+[A-Za-z]?)",

        r"(Sec\.\s*\d+)",

        r"(Article\s+\d+[A-Za-z]?)",

        r"(ARTICLE\s+\d+[A-Za-z]?)"

    ]


    for pattern in patterns:


        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )


        if match:

            return match.group(1).strip()


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
    "/",
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
def upload_document(

    file:UploadFile=File(...),

    db:Session=Depends(get_db)

):


    reader=PdfReader(file.file)



    title=os.path.splitext(
        file.filename
    )[0]



    pages=[]



    for page in reader.pages:


        text=(
            page.extract_text()
            or ""
        )


        pages.append(text)





    full_text="\n".join(pages)



    act_name=extract_act_name(
        title,
        full_text
    )



    page_chunks=split_pages(
        pages
    )



    chunks=[]



    current_chapter=None

    current_section=None

    current_title=None





    for item in page_chunks:


        content=item["content"]


        if not content.strip():

            continue





        chapter=extract_chapter(
            content
        )


        if chapter:

            current_chapter=chapter





        section=extract_section(
            content
        )


        if section:

            current_section=section

            current_title=extract_section_title(
                content
            )






        embedding=generate_embedding(
            content
        )





        metadata={


            "act_name":
                act_name,


            "document_type":
                "Uploaded PDF",


            "page_number":
                item["page_number"],



            "chapter":
                current_chapter,



            "section":
                current_section,



            "section_title":
                current_title

        }





        chunk=DocumentChunk(

            content=content,


            page_number=
                item["page_number"],



            section=current_section,



            metadata_json=metadata,



            embedding=embedding

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