from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.core.database import Base

class ModelConfig(Base):
    __tablename__ = "model_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stage = Column(String(20), nullable=False)  # extract|verify_grok|verify_gemini|analyze
    model_id = Column(String(200), nullable=False)  # OpenRouter model ID
    display_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    max_tokens = Column(Integer, default=4096)
    temperature = Column(Float, default=0.3)
    extra_params = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
