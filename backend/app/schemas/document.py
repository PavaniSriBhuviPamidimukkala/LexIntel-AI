from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class DocumentCreate(BaseModel):
    title: str
    content: str
    category: Optional[str] = None


class DocumentResponse(BaseModel):
    id: int
    title: str
    content: str
    category: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
