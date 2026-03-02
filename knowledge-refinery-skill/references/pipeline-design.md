# Pipeline Design — Knowledge Refinery

## 多模型协作管线

### 完整流程

```
用户输入
    │
    ▼
┌─ 预处理 (Preprocessor) ──────────────────────────┐
│                                                    │
│  截图 → PIL读取 → base64编码 → image_content       │
│  URL  → httpx抓取 → BeautifulSoup提取正文 → text   │
│  文本 → 直接使用 → text                            │
│                                                    │
│  输出: {"type": "image"|"text", "content": "..."}  │
└────────────────────┬───────────────────────────────┘
                     │
                     ▼
┌─ Stage 1: 提纯 (Extract) ────────────────────────┐
│  模型: anthropic/claude-3.5-sonnet                 │
│  超时: 30s                                         │
│                                                    │
│  截图输入:                                          │
│    messages: [{                                    │
│      "role": "user",                               │
│      "content": [                                  │
│        {"type": "image_url", "image_url":          │
│          {"url": "data:image/png;base64,{b64}"}},  │
│        {"type": "text", "text": extraction_prompt} │
│      ]                                             │
│    }]                                              │
│                                                    │
│  文本输入:                                          │
│    messages: [{                                    │
│      "role": "user",                               │
│      "content": extraction_prompt + "\n\n" + text  │
│    }]                                              │
│                                                    │
│  输出: Stage1Result (JSON)                         │
│  失败: 整条管线终止，返回错误                        │
└────────────────────┬───────────────────────────────┘
                     │
                     ▼
              ┌──────┴──────┐
              │ mode check  │
              └──┬──────┬───┘
          quick  │      │ deep
                 │      │
                 │      ▼
                 │  ┌─ Stage 2: 搜索验证 (Verify) ──────────┐
                 │  │                                         │
                 │  │  asyncio.gather (并行, return_exceptions)│
                 │  │                                         │
                 │  │  ┌─ Grok ──────────────┐                │
                 │  │  │ x-ai/grok-3         │                │
                 │  │  │ 超时: 60s           │                │
                 │  │  │ 任务: 社区+实时验证  │                │
                 │  │  └─────────────────────┘                │
                 │  │                                         │
                 │  │  ┌─ Gemini ────────────┐                │
                 │  │  │ google/gemini-2.5-pro│                │
                 │  │  │ 超时: 60s           │                │
                 │  │  │ 任务: 事实+技术验证  │                │
                 │  │  └─────────────────────┘                │
                 │  │                                         │
                 │  │  Merger: 合并验证结果                     │
                 │  │  → confirmed / conflicted / unverified   │
                 │  │                                         │
                 │  │  降级逻辑:                                │
                 │  │  Grok失败 → 只用Gemini                   │
                 │  │  Gemini失败 → 只用Grok                   │
                 │  │  都失败 → stage2=None, confidence-=0.2   │
                 │  └──────────────┬──────────────────────────┘
                 │                 │
                 ▼                 ▼
              ┌────────────────────┘
              │
              ▼
┌─ Stage 3: 深度分析 (Analyze) ────────────────────┐
│  模型: anthropic/claude-opus-4-6                   │
│  超时: 120s                                        │
│                                                    │
│  输入拼接:                                          │
│    1. profile_prompt (人格层，从DB读取)              │
│    2. analyze_prompt (任务层，从文件读取)             │
│    3. stage1_result (JSON)                         │
│    4. stage2_result (JSON, 快速模式为空)             │
│                                                    │
│  输出: Markdown + metadata JSON                    │
│                                                    │
│  降级: 失败 → 重试1次 → 仍失败用Sonnet替代           │
│        Sonnet替代时 confidence 自动 ≤ 0.5           │
└────────────────────┬───────────────────────────────┘
                     │
                     ▼
┌─ 后处理 (Post-processor) ────────────────────────┐
│                                                    │
│  1. 解析 Opus 输出，分离 MD 正文和 metadata JSON    │
│  2. 生成 slug: slugify(title)                      │
│  3. 生成文件名: {YYYYMMDD}-{slug}.md               │
│  4. 拼接 frontmatter + 正文，写入 knowledge-vault/  │
│  5. 保存截图到 attachments/{entry_id}/              │
│  6. 创建/关联 tags                                  │
│  7. 写入 knowledge_entries 记录                     │
│  8. 写入 pipeline_logs 记录 (每阶段一条)            │
│  9. 更新任务状态为 completed                        │
│                                                    │
└──────────────────────────────────────────────────┘
```

## 核心代码结构

### pipeline.py — 编排器

```python
import asyncio
import uuid
from datetime import datetime
from app.services.openrouter import OpenRouterClient
from app.services.extractor import Extractor
from app.services.verifier import Verifier
from app.services.analyzer import Analyzer
from app.services.md_writer import MDWriter
from app.services.preprocessor import Preprocessor

class PipelineOrchestrator:
    def __init__(self, db_session):
        self.db = db_session
        self.client = OpenRouterClient()
        self.preprocessor = Preprocessor()
        self.extractor = Extractor(self.client)
        self.verifier = Verifier(self.client)
        self.analyzer = Analyzer(self.client)
        self.md_writer = MDWriter()

    async def run(self, entry_id: str, input_data: dict, mode: str = "deep"):
        """
        input_data: {"type": "screenshot"|"url"|"text", "content": ...}
        mode: "quick" | "deep"
        """
        task_state = TaskState(entry_id=entry_id, mode=mode)

        try:
            # 预处理
            processed = await self.preprocessor.process(input_data)

            # Stage 1: 提纯
            task_state.set_stage("extract", "running")
            stage1 = await self.extractor.extract(processed)
            task_state.set_stage("extract", "completed")

            # Stage 2: 验证 (深度模式)
            stage2 = None
            confidence_penalty = 0.0

            if mode == "deep":
                task_state.set_stage("verify", "running")
                stage2, confidence_penalty = await self._run_verification(stage1)
                task_state.set_stage("verify", "completed")

            # Stage 3: 分析
            task_state.set_stage("analyze", "running")
            profile = await self._get_active_profile()
            analysis = await self.analyzer.analyze(
                stage1_result=stage1,
                stage2_result=stage2,
                profile_prompt=profile,
                confidence_penalty=confidence_penalty,
            )
            task_state.set_stage("analyze", "completed")

            # 后处理
            md_path = await self.md_writer.write(
                entry_id=entry_id,
                analysis=analysis,
                stage1=stage1,
                mode=mode,
            )
            await self._save_to_db(entry_id, analysis, md_path)
            task_state.set_completed()

        except Exception as e:
            task_state.set_failed(str(e))
            raise

    async def _run_verification(self, stage1):
        """并行执行 Grok + Gemini 验证，容错处理"""
        confidence_penalty = 0.0

        results = await asyncio.gather(
            self.verifier.verify_grok(stage1),
            self.verifier.verify_gemini(stage1),
            return_exceptions=True,
        )

        grok_result = results[0] if not isinstance(results[0], Exception) else None
        gemini_result = results[1] if not isinstance(results[1], Exception) else None

        if grok_result is None and gemini_result is None:
            # 两个都失败，降级
            confidence_penalty = 0.2
            return None, confidence_penalty

        merged = self.verifier.merge_results(grok_result, gemini_result)
        return merged, confidence_penalty
```

### 任务状态管理

```python
# 内存中的任务状态 (MVP阶段)
# V2 迁移到 Redis

from collections import defaultdict

_task_states: dict[str, dict] = {}

class TaskState:
    def __init__(self, entry_id: str, mode: str):
        self.task_id = str(uuid.uuid4())
        self.entry_id = entry_id
        self.state = {
            "task_id": self.task_id,
            "entry_id": entry_id,
            "status": "processing",
            "current_stage": "extract",
            "mode": mode,
            "stages": {
                "extract": {"status": "pending", "duration_ms": None, "cost_usd": None},
                "verify_grok": {"status": "skipped" if mode == "quick" else "pending", "duration_ms": None, "cost_usd": None},
                "verify_gemini": {"status": "skipped" if mode == "quick" else "pending", "duration_ms": None, "cost_usd": None},
                "analyze": {"status": "pending", "duration_ms": None, "cost_usd": None},
            },
            "total_cost_usd": 0.0,
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
        }
        _task_states[self.task_id] = self.state

    def set_stage(self, stage: str, status: str):
        self.state["stages"][stage]["status"] = status
        if stage in ("extract", "verify", "analyze"):
            self.state["current_stage"] = stage

    def set_completed(self):
        self.state["status"] = "completed"
        self.state["current_stage"] = "done"
        self.state["completed_at"] = datetime.utcnow().isoformat()

    def set_failed(self, error: str):
        self.state["status"] = "failed"
        self.state["error"] = error
```

## OpenRouter 调用细节

### 视觉模型调用 (截图)

```python
messages = [
    {
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/{ext};base64,{base64_data}"
                }
            },
            {
                "type": "text",
                "text": extraction_prompt
            }
        ]
    }
]

response = await client.chat(
    model="anthropic/claude-3.5-sonnet",
    messages=messages,
    max_tokens=2048,
    temperature=0.2,
)
```

### 文本模型调用

```python
messages = [
    {
        "role": "system",
        "content": system_prompt  # 人格层 + 任务层
    },
    {
        "role": "user",
        "content": user_content  # stage1 + stage2 数据
    }
]

response = await client.chat(
    model="anthropic/claude-opus-4-6",
    messages=messages,
    max_tokens=4096,
    temperature=0.4,
)
```

### OpenRouter 返回格式

```json
{
  "id": "gen-xxx",
  "model": "anthropic/claude-opus-4-6",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 1200,
    "completion_tokens": 800,
    "total_tokens": 2000
  }
}
```

提取内容: `response["choices"][0]["message"]["content"]`
提取 token: `response["usage"]`

## 成本计算

```python
# OpenRouter 返回中有 usage 信息
# 各模型价格 (per 1M tokens, 大致参考):
PRICING = {
    "anthropic/claude-3.5-sonnet": {"input": 3.0, "output": 15.0},
    "x-ai/grok-3": {"input": 3.0, "output": 15.0},
    "google/gemini-2.5-pro": {"input": 1.25, "output": 10.0},
    "anthropic/claude-opus-4-6": {"input": 15.0, "output": 75.0},
}

def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    prices = PRICING.get(model, {"input": 0, "output": 0})
    return (input_tokens * prices["input"] + output_tokens * prices["output"]) / 1_000_000
```

注意: 实际价格以 OpenRouter 为准，此处为估算参考。建议在 model_configs 表中维护价格字段。
