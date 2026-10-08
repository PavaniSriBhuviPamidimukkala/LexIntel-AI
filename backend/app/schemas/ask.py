from pydantic import BaseModel


class CitationResponse(BaseModel):
    source: str
    category: str | None = None
    page: int | None = None
    chunk_id: int
    quote: str
    relevance: float


class AskResponse(BaseModel):
    answer: str
    citations: list[CitationResponse]