---
name: knowledge-refinery-builder
description: Knowledge Refinery 碎片知识提炼系统构建技能。用于构建一个多模型协作的 AI 知识提炼 WebApp：用户上传截图/URL/文本，系统通过 OpenRouter 调用多个大模型（Sonnet 提纯 → Grok+Gemini 并行验证 → Opus 深度分析），输出 Obsidian 风格 MD 知识资产。技术栈为 React + TailwindCSS 前端、FastAPI 后端、PostgreSQL 数据库、Docker 部署。当用户提到 Knowledge Refinery、知识精炼、知识提炼系统、碎片知识管理、多模型管线、知识库构建时触发此 Skill。也适用于需要实现 OpenRouter 多模型编排、异步 AI 管线、MD 文件生成系统的场景。
---

# Knowledge Refinery Builder

构建碎片知识提炼系统——多模型协作 AI 管线 + Obsidian 风格知识库。

## 项目定位

**Knowledge Refinery** 不是文档柜，而是"战略分析师"。系统通过多阶段 AI 管线，将碎片信息自动提炼为结构化知识资产，完成"从点到线到面"的思考过程。

## 核心架构

```
用户输入 (截图/URL/文本)
    │
    ▼
┌──────────────────────────────────────────────┐
│  Stage 1: 提纯 (Sonnet 3.5)                  │
│  → 结构化信息提取 (JSON)                      │
└──────────┬───────────────────────────────────┘
           │
           ▼ (快速模式跳过)
┌──────────────────────────────────────────────┐
│  Stage 2: 搜索验证 (Grok ∥ Gemini 并行)      │
│  → 事实验证 + 社区评价 + 竞品分析              │
└──────────┬───────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│  Stage 3: 深度分析 (Opus 4.6)                 │
│  → 5维框架分析 + 个人背景关联 + MD 输出        │
└──────────┬───────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────────────┐
│  后处理: 生成 MD 文件 + 元数据入库 PG          │
└──────────────────────────────────────────────┘
```

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | React 18 + TailwindCSS + Vite |
| 后端 | FastAPI (Python 3.11+) + SQLAlchemy + Alembic |
| 数据库 | PostgreSQL 16 |
| AI 网关 | OpenRouter API (统一调用 Sonnet/Grok/Gemini/Opus) |
| 异步任务 | FastAPI BackgroundTasks |
| 存储 | 本地文件系统 (MD + 附件) |
| 部署 | Docker Compose → 宝塔面板 VPS |

## 工作流程

```
1. 阅读需求 → 详读 references/requirements.md (完整需求文档)
2. 数据库   → 参考 references/database-schema.md 创建模型和迁移
3. API      → 参考 references/api-spec.md 实现路由
4. 管线     → 参考 references/pipeline-design.md 实现多模型编排
5. Prompt   → 参考 references/prompts.md 部署提示词模板
6. 前端     → 按页面规划逐页实现
7. Docker   → 参考 references/docker-config.md 完成容器化
8. 部署     → 生成宝塔 Nginx 配置
```

**重要：开始任何编码前，必须先阅读 references/requirements.md 获取完整上下文。**

## 项目结构

```
knowledge-refinery/
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.example
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic/
│   │   └── versions/
│   ├── app/
│   │   ├── main.py                  # FastAPI 入口 + CORS + lifespan
│   │   ├── core/
│   │   │   ├── config.py            # Pydantic Settings (env)
│   │   │   ├── database.py          # async SQLAlchemy engine + session
│   │   │   └── pipeline.py          # 管线编排器 Orchestrator
│   │   ├── services/
│   │   │   ├── openrouter.py        # OpenRouter 统一客户端
│   │   │   ├── extractor.py         # Stage 1 提纯
│   │   │   ├── verifier.py          # Stage 2 验证 (Grok+Gemini)
│   │   │   ├── analyzer.py          # Stage 3 分析 (Opus)
│   │   │   ├── md_writer.py         # MD 文件生成
│   │   │   ├── preprocessor.py      # 输入预处理
│   │   │   └── tag_engine.py        # 标签管理
│   │   ├── models/                  # SQLAlchemy 模型
│   │   ├── schemas/                 # Pydantic schemas
│   │   ├── api/                     # 路由模块
│   │   └── prompts/                 # Prompt 模板文件 (任务层)
│   └── tests/
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── api/client.js
│       ├── components/
│       │   ├── layout/
│       │   ├── upload/
│       │   ├── entries/
│       │   └── settings/
│       ├── pages/
│       └── hooks/
│
├── knowledge-vault/                 # MD 主存储 (扁平+标签)
├── attachments/                     # 上传附件
└── nginx/
```

## 关键实现规范

### 1. OpenRouter 统一客户端

所有模型调用走同一个客户端，只切 model 参数：

```python
# backend/app/services/openrouter.py
import httpx
from app.core.config import settings

class OpenRouterClient:
    def __init__(self):
        self.base_url = settings.OPENROUTER_BASE_URL
        self.api_key = settings.OPENROUTER_API_KEY

    async def chat(self, model: str, messages: list, **kwargs) -> dict:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    **kwargs
                }
            )
            resp.raise_for_status()
            return resp.json()
```

### 2. 管线编排器

```python
# backend/app/core/pipeline.py 核心逻辑
import asyncio

class PipelineOrchestrator:
    async def run(self, entry_id, input_data, mode="deep"):
        # Stage 1: 提纯 (必须)
        stage1 = await self.extractor.extract(input_data)

        # Stage 2: 验证 (深度模式才执行，并行调用)
        stage2 = None
        if mode == "deep":
            grok_task = self.verifier.verify_grok(stage1)
            gemini_task = self.verifier.verify_gemini(stage1)
            results = await asyncio.gather(
                grok_task, gemini_task,
                return_exceptions=True  # 某个失败不影响另一个
            )
            stage2 = self.verifier.merge_results(results)

        # Stage 3: 深度分析 (必须)
        profile = await self.get_active_profile()
        analysis = await self.analyzer.analyze(stage1, stage2, profile)

        # 后处理: 生成 MD + 入库
        md_path = await self.md_writer.write(analysis)
        await self.save_entry(entry_id, analysis, md_path)
```

### 3. 双层 Prompt 体系

- **人格层**: 存 `user_profiles` 表，前端可编辑，描述用户背景
- **任务层**: 存 `backend/app/prompts/` 目录，每阶段独立文件
- 调用时动态拼接: `profile_prompt + task_prompt + stage_data`

详见 [references/prompts.md](references/prompts.md)

### 4. MD 文件规范

扁平结构，文件名: `{YYYYMMDD}-{slug}.md`

Frontmatter 包含: title, created, tags, confidence, maturity, actionability, pipeline_mode, related_projects, entry_id

正文 5 维框架:
1. 🔍 这是什么？(定义与本质)
2. 🛠️ 可以做什么？(核心功能)
3. 🎯 对我有什么帮助？(个人赋能) — 核心价值区
4. 📦 有什么具体案例？(实战参考)
5. 🚀 商业场景发散 (降维打击)

### 5. 降级容错

```
Grok 失败 → 只用 Gemini 继续
Gemini 失败 → 只用 Grok 继续
两个都失败 → 降级快速模式，confidence 下调 0.2
Opus 失败 → 重试1次 → 仍失败用 Sonnet 替代，confidence ≤ 0.5
Sonnet 失败 → 整条管线失败，保留原始输入可重试
```

### 6. 异步任务

上传后立即返回 task_id (202 Accepted)，管线在后台 BackgroundTasks 中执行，前端轮询 `/api/v1/pipeline/status/{task_id}` 获取进度。

### 7. 知识成熟度生命周期

```
seed → sprouted → mature → stale → archived
(AI生成)  (用户确认)  (已应用)  (90天未引用)  (手动归档)
```

定时任务每日检查，超过 90 天未引用自动标记 stale。

## 代码生成顺序

### 后端优先

```
1. core/config.py          → 环境变量 + Pydantic Settings
2. core/database.py        → async SQLAlchemy + session
3. models/*.py             → 6张表的 SQLAlchemy 模型
4. alembic 初始迁移         → 创建所有表
5. schemas/*.py            → Pydantic request/response schemas
6. services/openrouter.py  → OpenRouter 统一客户端
7. services/preprocessor.py → 输入预处理 (截图base64/URL抓取/文本)
8. services/extractor.py   → Stage 1 Sonnet 提纯
9. services/verifier.py    → Stage 2 Grok+Gemini 并行验证
10. services/analyzer.py   → Stage 3 Opus 深度分析
11. services/md_writer.py  → MD 生成 (frontmatter + 正文)
12. services/tag_engine.py → 标签自动创建和关联
13. core/pipeline.py       → 管线编排器
14. api/entries.py         → 知识条目 CRUD + 上传
15. api/pipeline.py        → 管线状态查询
16. api/tags.py            → 标签管理
17. api/profile.py         → 画像管理
18. api/config.py          → 模型配置
19. api/stats.py           → 统计
20. main.py                → FastAPI app + router 注册
21. prompts/*.txt          → 4个 Prompt 模板文件
```

### 前端

```
1. 项目初始化 (Vite + React + TailwindCSS)
2. api/client.js           → Axios 实例 + API 方法
3. components/layout/      → Sidebar + Header
4. pages/HomePage.jsx      → 上传入口 (三种输入 + 模式切换)
5. components/upload/      → UploadZone + UrlInput + TextInput + PipelineProgress
6. pages/EntriesPage.jsx   → 知识列表 (搜索/筛选/标签)
7. pages/EntryDetailPage.jsx → 知识详情 (MD渲染 + 元数据)
8. pages/TagsPage.jsx      → 标签管理
9. pages/SettingsPage.jsx  → 画像编辑 + 模型配置
10. pages/DashboardPage.jsx → 统计面板
```

### Docker

```
1. backend/Dockerfile
2. frontend/Dockerfile
3. docker-compose.yml (开发环境)
4. docker-compose.prod.yml (生产环境)
5. nginx/nginx.prod.conf (宝塔反代)
```

## 参考文档索引

| 文档 | 路径 | 内容 |
|------|------|------|
| 完整需求文档 | [references/requirements.md](references/requirements.md) | 项目全貌、架构图、开发计划 |
| 数据库设计 | [references/database-schema.md](references/database-schema.md) | 6张表详细字段定义 + SQL |
| API 规范 | [references/api-spec.md](references/api-spec.md) | 全部接口 + 请求响应示例 |
| 管线设计 | [references/pipeline-design.md](references/pipeline-design.md) | 多模型编排 + 降级策略 |
| Prompt 模板 | [references/prompts.md](references/prompts.md) | 人格层 + 4个任务层 Prompt |
| Docker 配置 | [references/docker-config.md](references/docker-config.md) | Compose + Dockerfile + Nginx |
