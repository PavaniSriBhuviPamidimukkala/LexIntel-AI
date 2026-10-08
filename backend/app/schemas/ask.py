from pydantic import BaseModel


class SourceResponse(BaseModel):
    title: str
    category: str
    score: float


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]