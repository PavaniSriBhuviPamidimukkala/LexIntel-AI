from sqlalchemy import (
    Column,
    Integer,
    Text,
    ForeignKey,
    DateTime,
    JSON,
    String
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from pgvector.sqlalchemy import Vector

from app.database import Base


class DocumentChunk(Base):

    __tablename__ = "document_chunks"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    document_id = Column(
        Integer,
        ForeignKey("legal_documents.id"),
        nullable=False
    )

    content = Column(
        Text,
        nullable=False
    )

    page_number = Column(
        Integer,
        nullable=False
    )

    section = Column(
        String,
        nullable=True
    )

    metadata_json = Column(
        JSON,
        nullable=True
    )

    embedding = Column(
        Vector(384),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    document = relationship(
        "LegalDocument",
        back_populates="chunks"
    )