from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

from pgvector.sqlalchemy import Vector

from app.database import Base


class LegalDocument(Base):
    __tablename__ = "legal_documents"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(
        String,
        nullable=False
    )

    content = Column(
        Text,
        nullable=False
    )

    category = Column(
        String,
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
