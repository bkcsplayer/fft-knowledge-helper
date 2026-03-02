from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class Attachment(Base):
    __tablename__ = "attachments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_entries.id", ondelete="CASCADE"), nullable=False)
    file_type = Column(String(20), nullable=False)  # image|pdf|html
    file_path = Column(String(1000), nullable=False)
    original_name = Column(String(500), nullable=True)
    file_size = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    entry = relationship("KnowledgeEntry", back_populates="attachments")
