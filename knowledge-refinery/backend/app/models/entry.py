import uuid
from sqlalchemy import Column, String, Float, Boolean, Text, DateTime, ForeignKey, Table, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

entry_tags = Table(
    "entry_tags",
    Base.metadata,
    Column("entry_id", UUID(as_uuid=True), ForeignKey("knowledge_entries.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)

class KnowledgeEntry(Base):
    __tablename__ = "knowledge_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    slug = Column(String(500), nullable=False, unique=True)
    category = Column(String(50), nullable=False)  # tech|business|tool|methodology|other
    md_file_path = Column(String(1000), nullable=False)
    input_type = Column(String(20), nullable=False)  # screenshot|url|text
    source_url = Column(String(2000), nullable=True)
    confidence = Column(Float, default=0.0)
    maturity = Column(String(20), default="seed")  # seed|sprouted|mature|stale|archived
    pipeline_mode = Column(String(10), nullable=False)  # quick|deep
    actionability = Column(String(10), default="medium")  # high|medium|low
    review_notes = Column(Text, nullable=True)
    is_favorite = Column(Boolean, default=False)
    last_referenced_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    tags = relationship("Tag", secondary="entry_tags", back_populates="entries")
    pipeline_logs = relationship("PipelineLog", back_populates="entry", cascade="all, delete-orphan")
    attachments = relationship("Attachment", back_populates="entry", cascade="all, delete-orphan")
