from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class NoteRead(BaseModel):
    id: str
    title: str
    done: bool
    created_at: datetime
