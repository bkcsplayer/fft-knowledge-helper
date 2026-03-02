# API Specification — Knowledge Refinery

## Base URL

```
开发: http://localhost:8000/api/v1
生产: https://your-domain.com/api/v1
```

## 1. 知识条目 (Entries)

### POST /entries/upload — 上传并触发管线

```python
# 路由定义
@router.post("/entries/upload", status_code=202)
async def upload_entry(
    input_type: str = Form(...),           # screenshot | url | text
    pipeline_mode: str = Form("deep"),     # quick | deep
    file: UploadFile = File(None),         # 截图 (input_type=screenshot)
    url: str = Form(None),                 # URL (input_type=url)
    text: str = Form(None),               # 文本 (input_type=text)
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
```

```json
// Response 202
{
  "task_id": "uuid-xxx",
  "entry_id": "uuid-xxx",
  "status": "processing",
  "message": "Pipeline started in deep mode",
  "estimated_seconds": 45
}
```

### GET /entries — 知识列表

```
Query Parameters:
  page=1           (default: 1)
  per_page=20      (default: 20, max: 100)
  search=keyword   (标题全文搜索)
  tags=AI,tool     (逗号分隔，AND 逻辑)
  category=tech    (分类筛选)
  maturity=seed,sprouted  (成熟度筛选，逗号分隔)
  confidence_min=0.7  (最低可信度)
  actionability=high  (可操作性)
  is_favorite=true    (收藏)
  sort_by=created_at  (created_at|confidence|updated_at)
  sort_order=desc     (asc|desc)
```

```json
// Response 200
{
  "items": [
    {
      "id": "uuid-xxx",
      "title": "Ollama - 本地大模型运行框架",
      "category": "tech",
      "confidence": 0.85,
      "maturity": "seed",
      "actionability": "high",
      "pipeline_mode": "deep",
      "is_favorite": false,
      "tags": [
        {"id": 1, "name": "AI", "color": "#3B82F6"},
        {"id": 2, "name": "本地部署", "color": "#10B981"}
      ],
      "created_at": "2026-03-01T10:00:00Z",
      "updated_at": "2026-03-01T10:00:00Z"
    }
  ],
  "total": 156,
  "page": 1,
  "per_page": 20,
  "total_pages": 8
}
```

### GET /entries/{id} — 知识详情

```json
// Response 200
{
  "id": "uuid-xxx",
  "title": "Ollama - 本地大模型运行框架",
  "slug": "ollama-local-llm-framework",
  "category": "tech",
  "md_file_path": "20260301-ollama-local-llm-framework.md",
  "md_content": "## 🔍 这是什么？...",   // 读取 MD 文件内容
  "input_type": "screenshot",
  "source_url": null,
  "confidence": 0.85,
  "maturity": "seed",
  "pipeline_mode": "deep",
  "actionability": "high",
  "review_notes": "社区活跃度评估有分歧",
  "is_favorite": false,
  "last_referenced_at": null,
  "tags": [...],
  "attachments": [
    {"id": 1, "file_type": "image", "original_name": "screenshot.png", "file_size": 245000}
  ],
  "pipeline_summary": {
    "total_cost_usd": 0.045,
    "total_duration_ms": 32000,
    "stages_completed": 4
  },
  "created_at": "2026-03-01T10:00:00Z",
  "updated_at": "2026-03-01T10:00:00Z"
}
```

### PATCH /entries/{id} — 更新条目

```json
// Request
{
  "maturity": "sprouted",     // 可选
  "is_favorite": true,        // 可选
  "tags": [1, 2, 5],          // 可选，tag IDs (全量替换)
  "review_notes": "已确认"     // 可选
}

// Response 200
{ "id": "uuid-xxx", "maturity": "sprouted", "updated_at": "..." }
```

### DELETE /entries/{id} — 删除条目

删除 PG 记录 + MD 文件 + 附件。Response 204 No Content。

### GET /entries/{id}/md — 获取原始 MD

```
Response 200: text/markdown
Content-Type: text/markdown; charset=utf-8

---
title: "Ollama..."
...
---

## 🔍 这是什么？
...
```

### PUT /entries/{id}/md — 更新 MD 内容

```json
// Request
{ "content": "---\ntitle: ...\n---\n\n## 🔍 这是什么？\n..." }

// Response 200
{ "id": "uuid-xxx", "message": "MD file updated" }
```

### POST /entries/{id}/reanalyze — 重新分析

```json
// Request
{ "pipeline_mode": "deep" }

// Response 202
{ "task_id": "uuid-new", "message": "Re-analysis started" }
```

---

## 2. 管线状态 (Pipeline)

### GET /pipeline/status/{task_id}

```json
// Response 200
{
  "task_id": "uuid-xxx",
  "entry_id": "uuid-xxx",
  "status": "processing",      // queued|processing|completed|failed
  "current_stage": "verify",   // extract|verify|analyze|done
  "stages": {
    "extract": {"status": "completed", "duration_ms": 3200, "cost_usd": 0.003},
    "verify_grok": {"status": "completed", "duration_ms": 8100, "cost_usd": 0.012},
    "verify_gemini": {"status": "processing", "duration_ms": null, "cost_usd": null},
    "analyze": {"status": "pending", "duration_ms": null, "cost_usd": null}
  },
  "total_cost_usd": 0.015,
  "started_at": "2026-03-01T10:00:00Z",
  "completed_at": null
}
```

### GET /pipeline/logs/{entry_id}

```json
// Response 200
{
  "entry_id": "uuid-xxx",
  "logs": [
    {
      "id": 1,
      "stage": "extract",
      "model_used": "anthropic/claude-3.5-sonnet",
      "input_tokens": 1200,
      "output_tokens": 450,
      "cost_usd": 0.003,
      "duration_ms": 3200,
      "status": "success",
      "created_at": "2026-03-01T10:00:01Z"
    },
    ...
  ],
  "total_cost_usd": 0.045,
  "total_duration_ms": 32000
}
```

---

## 3. 标签 (Tags)

### GET /tags

```json
// Query: ?sort_by=usage_count&sort_order=desc
// Response 200
{
  "items": [
    {"id": 1, "name": "AI", "color": "#3B82F6", "usage_count": 45},
    {"id": 2, "name": "本地部署", "color": "#10B981", "usage_count": 12}
  ]
}
```

### POST /tags

```json
// Request
{ "name": "新标签", "color": "#F59E0B" }
// Response 201
{ "id": 10, "name": "新标签", "color": "#F59E0B", "usage_count": 0 }
```

### PATCH /tags/{id}

```json
// Request
{ "name": "改名", "color": "#EF4444" }
```

### DELETE /tags/{id}

Response 204. 自动解除所有关联。

---

## 4. 用户画像 (Profile)

### GET /profile

```json
// Response 200
{
  "id": 1,
  "profile_name": "default",
  "profile_prompt": "你是一个具有商业头脑的技术战略分析师...",
  "is_active": true,
  "updated_at": "2026-03-01T10:00:00Z"
}
```

### PUT /profile

```json
// Request
{
  "profile_name": "default",
  "profile_prompt": "更新后的 Prompt 内容..."
}
```

---

## 5. 系统配置 (Config)

### GET /config/models

```json
// Response 200
{
  "models": [
    {
      "id": 1,
      "stage": "extract",
      "model_id": "anthropic/claude-3.5-sonnet",
      "display_name": "Claude Sonnet 3.5 (提纯)",
      "is_active": true,
      "max_tokens": 2048,
      "temperature": 0.2
    },
    ...
  ]
}
```

### PUT /config/models/{id}

```json
// Request
{
  "model_id": "anthropic/claude-3.5-sonnet-20241022",
  "max_tokens": 3000,
  "temperature": 0.3
}
```

---

## 6. 统计 (Stats)

### GET /stats

```json
// Response 200
{
  "total_entries": 156,
  "by_category": {"tech": 80, "tool": 45, "business": 20, "methodology": 8, "other": 3},
  "by_maturity": {"seed": 30, "sprouted": 60, "mature": 40, "stale": 20, "archived": 6},
  "by_actionability": {"high": 50, "medium": 70, "low": 36},
  "avg_confidence": 0.78,
  "total_cost_usd": 12.50,
  "cost_this_month_usd": 3.20,
  "entries_this_week": 8,
  "top_tags": [
    {"name": "AI", "count": 45},
    {"name": "FastAPI", "count": 23}
  ],
  "stale_entries_count": 20
}
```

---

## Pydantic Schemas 参考

```python
# schemas/entry.py
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from typing import Optional

class EntryCreate(BaseModel):
    input_type: str  # screenshot|url|text
    pipeline_mode: str = "deep"

class EntryUpdate(BaseModel):
    maturity: Optional[str] = None
    is_favorite: Optional[bool] = None
    tags: Optional[list[int]] = None
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
    tags: list[dict]
    created_at: datetime
    updated_at: datetime

class EntryDetail(EntryBrief):
    slug: str
    md_file_path: str
    md_content: str
    input_type: str
    source_url: Optional[str]
    review_notes: Optional[str]
    last_referenced_at: Optional[datetime]
    attachments: list[dict]
    pipeline_summary: dict

class EntryList(BaseModel):
    items: list[EntryBrief]
    total: int
    page: int
    per_page: int
    total_pages: int

class PipelineStatus(BaseModel):
    task_id: str
    entry_id: str
    status: str
    current_stage: str
    stages: dict
    total_cost_usd: float
    started_at: datetime
    completed_at: Optional[datetime]
```
