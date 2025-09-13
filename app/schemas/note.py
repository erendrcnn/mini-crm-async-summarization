from pydantic import BaseModel, Field
from typing import Literal, Optional


class NoteCreate(BaseModel):
    raw_text: str = Field(..., min_length=1, max_length=10000, description="The text content to summarize")


class NoteOut(BaseModel):
    id: int
    raw_text: str
    summary: Optional[str] = None
    status: Literal["queued", "processing", "done", "failed"]
    attempts: int = 0

    model_config = {
        "from_attributes": True,
    }
