from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any

class AttachmentBase(BaseModel):
    id: int
    file_type: str
    original_name: Optional[str] = None
    file_size: int

class Attachment(AttachmentBase):
    class Config:
        from_attributes = True

class TagBrief(BaseModel):
    id: int
    name: str
    color: str

class EntryCreate(BaseModel):
    input_type: str  # screenshot|url|text
    pipeline_mode: str = "deep"

class EntryUpdate(BaseModel):
    maturity: Optional[str] = None
    is_favorite: Optional[bool] = None
    tags: Optional[List[int]] = None
    review_notes: Optional[str] = None

class EntryBrief(BaseModel):
    id: UUID
    title: str
    category: str
    confidence: float
    maturity: str
    actionability: str
    pipeline_mode: str
    is_favorite: bool
    tags: List[TagBrief] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class EntryDetail(EntryBrief):
    slug: str
    md_file_path: str
    md_content: Optional[str] = None
    input_type: str
    source_url: Optional[str] = None
    review_notes: Optional[str] = None
    last_referenced_at: Optional[datetime] = None
    attachments: List[Attachment] = []
    pipeline_summary: Dict[str, Any] = {}

    class Config:
        from_attributes = True

class EntryList(BaseModel):
    items: List[EntryBrief]
    total: int
    page: int
    per_page: int
    total_pages: int
