from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ChatHistoryResponse(BaseModel):
    id: int
    question: str
    answer: str
    citations: list[dict[str, Any]]
    retrieval_succeeded: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
