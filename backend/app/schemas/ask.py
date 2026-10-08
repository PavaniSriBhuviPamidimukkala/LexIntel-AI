from pydantic import BaseModel


class SourceResponse(BaseModel):
    title: str
    category: str
    page_number: int | None = None
    score: float


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]