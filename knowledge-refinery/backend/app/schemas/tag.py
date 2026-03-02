from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TagCreate(BaseModel):
    name: str
    color: Optional[str] = "#6B7280"

class TagUpdate(BaseModel):
    name: Optional[str] = None
    color: Optional[str] = None

class TagResponse(BaseModel):
    id: int
    name: str
    color: str
    usage_count: int
    created_at: datetime

    class Config:
        from_attributes = True
