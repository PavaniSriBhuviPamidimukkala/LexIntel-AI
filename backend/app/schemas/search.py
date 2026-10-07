from pydantic import BaseModel
from typing import Optional


class SearchResult(BaseModel):
    id: int
    title: str
    category: Optional[str] = None
    snippet: str
    score: float