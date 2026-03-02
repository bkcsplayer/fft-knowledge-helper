# Database Schema — Knowledge Refinery

## ER 关系

```
user_profiles 1 ──── N knowledge_entries
knowledge_entries N ──── N tags (through entry_tags)
knowledge_entries 1 ──── N pipeline_logs
knowledge_entries 1 ──── N attachments
```

## SQLAlchemy 模型参考

### user_profiles

```python
class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    profile_name = Column(String(100), nullable=False, default="default")
    profile_prompt = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

### knowledge_entries

```python
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
```

### tags

```python
class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    color = Column(String(7), default="#6B7280")
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    entries = relationship("KnowledgeEntry", secondary="entry_tags", back_populates="tags")
```

### entry_tags

```python
entry_tags = Table(
    "entry_tags",
    Base.metadata,
    Column("entry_id", UUID(as_uuid=True), ForeignKey("knowledge_entries.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)
```

### attachments

```python
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
```

### pipeline_logs

```python
class PipelineLog(Base):
    __tablename__ = "pipeline_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entry_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_entries.id", ondelete="CASCADE"), nullable=False)
    stage = Column(String(20), nullable=False)  # extract|verify_grok|verify_gemini|analyze
    model_used = Column(String(100), nullable=False)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    duration_ms = Column(Integer, default=0)
    raw_response = Column(JSONB, nullable=True)
    status = Column(String(20), default="pending")  # pending|running|success|failed|timeout
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    entry = relationship("KnowledgeEntry", back_populates="pipeline_logs")
```

### model_configs

```python
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
```

## 初始化种子数据

```python
# 默认模型配置
DEFAULT_MODELS = [
    {
        "stage": "extract",
        "model_id": "anthropic/claude-3.5-sonnet",
        "display_name": "Claude Sonnet 3.5 (提纯)",
        "max_tokens": 2048,
        "temperature": 0.2,
    },
    {
        "stage": "verify_grok",
        "model_id": "x-ai/grok-3",
        "display_name": "Grok 3 (社区验证)",
        "max_tokens": 2048,
        "temperature": 0.3,
    },
    {
        "stage": "verify_gemini",
        "model_id": "google/gemini-2.5-pro",
        "display_name": "Gemini 2.5 Pro (事实验证)",
        "max_tokens": 2048,
        "temperature": 0.2,
    },
    {
        "stage": "analyze",
        "model_id": "anthropic/claude-opus-4-6",
        "display_name": "Claude Opus 4.6 (深度分析)",
        "max_tokens": 4096,
        "temperature": 0.4,
    },
]
```

## 索引建议

```sql
-- 加速搜索和筛选
CREATE INDEX idx_entries_category ON knowledge_entries(category);
CREATE INDEX idx_entries_maturity ON knowledge_entries(maturity);
CREATE INDEX idx_entries_confidence ON knowledge_entries(confidence);
CREATE INDEX idx_entries_created_at ON knowledge_entries(created_at DESC);
CREATE INDEX idx_entries_title_search ON knowledge_entries USING gin(to_tsvector('english', title));
CREATE INDEX idx_tags_name ON tags(name);
CREATE INDEX idx_pipeline_logs_entry ON pipeline_logs(entry_id);
CREATE INDEX idx_pipeline_logs_stage ON pipeline_logs(stage);
```
