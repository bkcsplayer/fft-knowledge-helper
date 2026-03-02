# Knowledge Refinery — 碎片知识提炼系统

## 项目开发报告 v1.0

---

## 1. 项目概述

### 1.1 项目名称

**Knowledge Refinery** (知识精炼厂)

### 1.2 一句话描述

一个多模型协作的 AI 知识提炼系统——用户上传截图/URL/文本，系统通过多阶段 AI 管线自动完成「提纯 → 搜索验证 → 深度分析」，输出结构化的 Obsidian 风格 MD 知识资产。

### 1.3 核心价值

**从"看到一个点"，到"联想到一条线"，最后"铺开成一个面"的自动化思考引擎。**

系统不是文档柜，而是"战略分析师"。每一条输入都会经过 AI 的提纯、事实验证、个人背景关联分析和商业场景发散，最终沉淀为可 Obsidian 阅读的 MD 知识资产。

### 1.4 目标用户

个人使用（单用户系统），部署在个人 VPS 上，随时随地通过 Web 访问。

### 1.5 技术栈

| 层 | 技术 |
|---|---|
| 前端 | React 18 + TailwindCSS |
| 后端 | FastAPI (Python 3.11+) |
| 数据库 | PostgreSQL 16 |
| 任务队列 | FastAPI BackgroundTasks（MVP）→ Celery + Redis（V2） |
| AI 网关 | OpenRouter API（统一调用多模型） |
| 文件存储 | 本地文件系统（MD 文件 + 上传图片） |
| 容器化 | Docker + Docker Compose |
| 开发工具 | Cursor |
| 部署 | Windows 本地测试 → VPS 宝塔面板 |

---

## 2. 系统架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────────────────┐ │
│  │ 上传入口  │ │ 知识列表  │ │ 知识详情  │ │ Profile 设置页面   │ │
│  │截图/URL/  │ │搜索/筛选/ │ │MD渲染/   │ │人格层Prompt/      │ │
│  │文本粘贴   │ │标签过滤   │ │状态管理   │ │模型配置           │ │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────────┬───────────┘ │
└───────┼────────────┼────────────┼─────────────────┼─────────────┘
        │            │            │                 │
        ▼            ▼            ▼                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                              │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   API Router Layer                        │   │
│  │  /api/v1/entries   /api/v1/tags   /api/v1/profile        │   │
│  │  /api/v1/pipeline  /api/v1/stats  /api/v1/config         │   │
│  └──────────────────────┬───────────────────────────────────┘   │
│                         │                                        │
│  ┌──────────────────────▼───────────────────────────────────┐   │
│  │              Pipeline Orchestrator (编排器)                │   │
│  │                                                           │   │
│  │  ┌─────────┐   ┌──────────────┐   ┌─────────────────┐   │   │
│  │  │ Stage 1 │──▶│   Stage 2    │──▶│     Stage 3     │   │   │
│  │  │ 提纯    │   │  搜索验证     │   │   深度分析+定稿  │   │   │
│  │  │Sonnet   │   │Grok ∥ Gemini │   │   Opus 4.6      │   │   │
│  │  │ 3.5     │   │  (并行调用)   │   │                 │   │   │
│  │  └─────────┘   └──────────────┘   └─────────────────┘   │   │
│  │                                                           │   │
│  │  模式: [快速] Sonnet → Opus    [深度] Sonnet → Grok+Gemini → Opus │
│  └──────────────────────────────────────────────────────────┘   │
│                         │                                        │
│  ┌──────────────────────▼───────────────────────────────────┐   │
│  │            OpenRouter Unified Client                       │   │
│  │  统一封装所有模型调用，只切换 model 参数                      │   │
│  └──────────────────────┬───────────────────────────────────┘   │
│                         │                                        │
│  ┌──────────────────────▼───────────────────────────────────┐   │
│  │              Services Layer                                │   │
│  │  ┌────────────┐ ┌────────────┐ ┌───────────────────────┐ │   │
│  │  │ MD Writer  │ │ Tag Engine │ │ Profile Injector       │ │   │
│  │  │ 写入MD文件  │ │ 自动打标签  │ │ 动态拼接人格层Prompt  │ │   │
│  │  └────────────┘ └────────────┘ └───────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
        │                                       │
        ▼                                       ▼
┌───────────────┐                    ┌─────────────────────┐
│  PostgreSQL   │                    │  knowledge-vault/   │
│  (元数据索引)  │                    │  (MD文件主存储)      │
│               │                    │  扁平结构+标签       │
│  entries      │                    │  Obsidian兼容       │
│  tags         │                    │                     │
│  profiles     │                    │  *.md (frontmatter) │
│  pipeline_logs│                    │                     │
└───────────────┘                    └─────────────────────┘
```

### 2.2 多模型协作管线

```
用户输入 (截图/URL/文本)
     │
     ▼
┌─────────────────────────────────────────┐
│ 预处理层 (Pre-processor)                 │
│                                          │
│  截图 → base64 编码，准备发给视觉模型     │
│  URL  → 后端抓取网页内容，提取正文        │
│  文本 → 直接传入                         │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│ Stage 1: 提纯 (Extract)                 │
│ 模型: claude-3.5-sonnet (via OpenRouter) │
│                                          │
│ 输入: 原始内容                            │
│ 输出 (JSON):                             │
│   - title: 识别出的主题名称               │
│   - category: 技术/商业/工具/方法论/其他   │
│   - raw_summary: 原始信息摘要             │
│   - key_features: [关键特性列表]          │
│   - tech_stack: [涉及的技术栈]            │
│   - entities: [识别出的实体/产品/公司]     │
│   - initial_tags: [初步标签建议]          │
│   - search_queries: [建议的验证搜索词]     │
│                                          │
│ Prompt: 任务层 - extraction_prompt.txt   │
└─────────────┬───────────────────────────┘
              │
              ▼ (快速模式跳过 Stage 2)
┌─────────────────────────────────────────┐
│ Stage 2: 搜索验证 (Verify) — 并行执行    │
│                                          │
│ ┌─────────────────────────────────────┐ │
│ │ Grok (x-ai/grok-3)                 │ │
│ │ 任务: 社区评价 + 实时动态            │ │
│ │ - 项目/技术是否真实存在？             │ │
│ │ - 社区评价如何？X/Twitter 讨论热度？ │ │
│ │ - 有没有已知的坑或争议？             │ │
│ │ - 最新版本和维护状态？               │ │
│ │                                     │ │
│ │ Prompt: 任务层 - verify_grok.txt    │ │
│ └─────────────────────────────────────┘ │
│                                          │
│ ┌─────────────────────────────────────┐ │
│ │ Gemini (google/gemini-2.5-pro)      │ │
│ │ 任务: 事实验证 + 技术细节            │ │
│ │ - 官方文档验证                       │ │
│ │ - GitHub 数据 (stars/forks/issues)  │ │
│ │ - 竞品和替代方案                     │ │
│ │ - Stage 1 提取信息的准确性校验       │ │
│ │                                     │ │
│ │ Prompt: 任务层 - verify_gemini.txt  │ │
│ └─────────────────────────────────────┘ │
│                                          │
│ 汇总器 (Merger):                         │
│ - 合并两家验证结果                        │
│ - 标记一致项 (confirmed)                  │
│ - 标记矛盾项 (conflicted)                │
│ - 标记未验证项 (unverified)               │
│                                          │
│ 输出 (JSON):                             │
│   - verified_facts: [已确认事实]          │
│   - conflicts: [矛盾点]                  │
│   - community_sentiment: 正面/中性/负面   │
│   - freshness: 信息新鲜度评估             │
│   - competitors: [竞品列表]               │
│   - risk_flags: [风险提示]                │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│ Stage 3: 深度分析 + 定稿 (Analyze)       │
│ 模型: claude-opus-4-6 (via OpenRouter)   │
│                                          │
│ 输入:                                    │
│   - Stage 1 提纯结果 (JSON)              │
│   - Stage 2 验证结果 (JSON) [深度模式]    │
│   - 人格层 Profile Prompt                │
│                                          │
│ 输出: 5维分析框架 (Markdown)              │
│   1. 🔍 这是什么？(定义与本质)            │
│   2. 🛠️ 可以做什么？(核心功能)           │
│   3. 🎯 对我有什么帮助？(个人赋能)        │
│   4. 📦 有什么具体案例？(实战参考)        │
│   5. 🚀 商业场景发散 (降维打击)           │
│   + confidence 评分 (0-1)                │
│   + 最终标签列表                          │
│   + 成熟度初始状态                        │
│                                          │
│ Prompt: 人格层 + 任务层 - analyze.txt    │
└─────────────┬───────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│ 后处理 (Post-processor)                  │
│                                          │
│ 1. 生成 MD 文件 (含 frontmatter)         │
│ 2. 写入 knowledge-vault/ 目录            │
│ 3. 元数据写入 PostgreSQL                  │
│ 4. 原始截图存入 attachments/ 目录         │
│ 5. Pipeline 日志写入 pipeline_logs 表     │
└─────────────────────────────────────────┘
```

---

## 3. Prompt 架构

### 3.1 双层 Prompt 体系

#### 人格层 (Profile Prompt) — 所有阶段共享

存储在数据库 `user_profiles` 表中，前端可编辑，每次调用动态拼接。

```
你是一个具有商业头脑的技术战略分析师，服务于一个特定用户。以下是该用户的完整背景：

【基本信息】
- 身份：全栈开发者 + 太阳能板安装业务经营者
- 技术栈：React, TailwindCSS, FastAPI, PostgreSQL, Docker, Python
- 硬件：本地开发 PC 配备 RTX 3090 显卡
- 开发工具：Cursor, Claude Code, VS Code

【商业背景】
- 经营太阳能板安装业务，团队在多地进行现场安装
- 管理高价值序列化设备（GPU 矿机等）
- 有跨国物流/集运业务经验
- 运营基地在 Torrington，使用 Toyota Tundra 进行移动库存管理

【在建项目】
- Nexus EAM：个人库存管理系统（React + FastAPI + PostgreSQL）
- Family CFO：加拿大家庭财务管理系统，含 AI 文档解析
- 太阳能 CRM：施工团队管理、项目阶段跟踪、资产管理

【分析偏好】
- 关注实际落地可行性，不要空谈理论
- 尤其关注能降本增效的技术和工具
- 重视数据隐私和本地化部署方案
- 喜欢跨领域关联思考（技术 × 商业 × 个人项目）
```

#### 任务层 (Task Prompts) — 每阶段独立

存储在 `backend/app/prompts/` 目录下，独立文件管理。

**extraction_prompt.txt** — Stage 1 提纯

```
你是一个信息提纯专家。你的任务是从用户提供的内容中提取结构化信息。

输入可能是：截图中的文字、网页内容、或用户直接粘贴的文本。

请严格按以下 JSON 格式输出，不要包含任何其他内容：

{
  "title": "识别出的主题/产品/技术名称",
  "category": "tech|business|tool|methodology|other",
  "raw_summary": "用 2-3 句话概括原始内容的核心信息",
  "key_features": ["特性1", "特性2", "特性3"],
  "tech_stack": ["涉及的技术1", "技术2"],
  "entities": ["识别出的产品名/公司名/人名"],
  "initial_tags": ["标签1", "标签2", "标签3"],
  "search_queries": ["建议用于验证的搜索关键词1", "关键词2"]
}

注意：
- 如果信息不完整，用 null 填充，不要编造
- search_queries 要具体到可以直接用于搜索引擎的程度
- tags 要考虑后续检索价值，尽量用英文或通用术语
```

**verify_grok.txt** — Stage 2 Grok 验证

```
你是一个信息验证专家，擅长通过互联网搜索验证技术信息的真实性和时效性。

以下是 Stage 1 提取的结构化信息：
{stage1_result}

请针对以上信息完成以下验证任务：

1. 【存在性验证】这个技术/产品/项目是否真实存在？当前状态如何？
2. 【社区评价】在 X/Twitter、Reddit、HackerNews 上的讨论热度和评价倾向
3. 【风险识别】有没有已知的安全漏洞、性能陷阱、或社区争议？
4. 【时效性】信息是最新的吗？最近一次更新/发布是什么时候？

请严格按以下 JSON 格式输出：
{
  "existence_verified": true/false,
  "current_status": "active|deprecated|beta|unknown",
  "community_sentiment": "positive|neutral|negative|mixed",
  "discussion_highlights": ["要点1", "要点2"],
  "known_issues": ["问题1", "问题2"],
  "last_update": "YYYY-MM or unknown",
  "confidence": 0.0-1.0
}
```

**verify_gemini.txt** — Stage 2 Gemini 验证

```
你是一个技术事实核查专家，擅长通过官方文档和权威来源验证技术细节。

以下是 Stage 1 提取的结构化信息：
{stage1_result}

请针对以上信息完成以下验证任务：

1. 【官方验证】通过官方网站/GitHub 仓库验证基本信息
2. 【数据指标】GitHub stars/forks/issues 数量，npm/PyPI 下载量
3. 【竞品分析】主要竞品或替代方案是什么？各自优劣？
4. 【准确性】Stage 1 提取的信息有没有事实性错误？

请严格按以下 JSON 格式输出：
{
  "official_verified": true/false,
  "github_stats": {"stars": N, "forks": N, "open_issues": N},
  "download_stats": "描述",
  "competitors": [{"name": "竞品名", "comparison": "简要对比"}],
  "fact_corrections": ["纠正1", "纠正2"],
  "additional_context": "补充的重要背景信息",
  "confidence": 0.0-1.0
}
```

**analyze_prompt.txt** — Stage 3 Opus 深度分析

```
{profile_prompt}

---

你现在收到了一条经过提纯和验证的知识碎片，需要将其转化为对该用户有极高价值的知识资产。

【Stage 1 提纯结果】
{stage1_result}

【Stage 2 验证结果】(如果是快速模式则为空)
{stage2_result}

请按照以下 5 维框架进行深度分析，输出 Markdown 格式：

---

## 🔍 这是什么？(定义与本质)
用一段话说清楚这个东西的本质，不要抄官方介绍，要用"给一个技术背景的商人解释"的口吻。

## 🛠️ 可以做什么？(核心功能)
列出 3-5 个最核心的功能点，每个功能点用一句话说清价值。

## 🎯 对我有什么帮助？(个人赋能)
**这是最核心的部分。** 结合用户的背景（技术栈、在建项目、商业场景），分析这个知识点如何直接赋能用户。至少给出 2 个具体的应用场景。

## 📦 有什么具体案例？(实战参考)
列出 2-3 个真实或合理推演的应用案例，优先引用验证阶段发现的真实案例。

## 🚀 商业场景发散 (降维打击)
结合用户的商业背景（太阳能安装、设备管理、物流集运），发散出 2-3 个可落地的商业应用场景。每个场景要具体到"怎么用、用在哪、解决什么问题"。

---

同时，请在分析结束后附加以下元数据（JSON 格式，用 ```json 代码块包裹）：

{
  "confidence": 0.0-1.0,
  "tags": ["最终标签列表"],
  "maturity": "seed",
  "related_projects": ["关联的用户在建项目"],
  "actionability": "high|medium|low",
  "review_notes": "需要用户关注的不确定点"
}
```

---

## 4. 数据库设计

### 4.1 ER 关系

```
user_profiles 1 ──── N knowledge_entries
knowledge_entries N ──── N tags (through entry_tags)
knowledge_entries 1 ──── N pipeline_logs
knowledge_entries 1 ──── N attachments
```

### 4.2 表结构

#### 表: user_profiles (用户画像)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| profile_name | VARCHAR(100) | 画像名称（预留多画像） |
| profile_prompt | TEXT | 人格层 Prompt 内容 |
| is_active | BOOLEAN | 是否为当前活跃画像 |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

#### 表: knowledge_entries (知识条目 — 索引层)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| title | VARCHAR(500) | 知识标题 |
| slug | VARCHAR(500) | MD 文件名 (URL-safe) |
| category | VARCHAR(50) | 分类: tech/business/tool/methodology/other |
| md_file_path | VARCHAR(1000) | MD 文件相对路径 |
| input_type | VARCHAR(20) | 输入类型: screenshot/url/text |
| source_url | VARCHAR(2000) | 原始 URL（如适用） |
| confidence | FLOAT | AI 分析可信度 (0-1) |
| maturity | VARCHAR(20) | 成熟度: seed/sprouted/mature/stale/archived |
| pipeline_mode | VARCHAR(10) | 分析模式: quick/deep |
| actionability | VARCHAR(10) | 可操作性: high/medium/low |
| review_notes | TEXT | AI 标记的不确定点 |
| is_favorite | BOOLEAN | 是否收藏 |
| last_referenced_at | TIMESTAMPTZ | 最后一次被引用的时间 |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

#### 表: tags (标签)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| name | VARCHAR(100) | 标签名 (唯一) |
| color | VARCHAR(7) | 标签颜色 (hex) |
| usage_count | INT | 使用次数（冗余字段，加速统计） |
| created_at | TIMESTAMPTZ | 创建时间 |

#### 表: entry_tags (知识-标签关联)

| 字段 | 类型 | 说明 |
|------|------|------|
| entry_id | UUID | 外键 → knowledge_entries.id |
| tag_id | INT | 外键 → tags.id |

复合主键: (entry_id, tag_id)

#### 表: attachments (附件)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| entry_id | UUID | 外键 → knowledge_entries.id |
| file_type | VARCHAR(20) | 文件类型: image/pdf/html |
| file_path | VARCHAR(1000) | 文件存储路径 |
| original_name | VARCHAR(500) | 原始文件名 |
| file_size | INT | 文件大小 (bytes) |
| created_at | TIMESTAMPTZ | 创建时间 |

#### 表: pipeline_logs (管线日志)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| entry_id | UUID | 外键 → knowledge_entries.id |
| stage | VARCHAR(20) | 阶段: extract/verify_grok/verify_gemini/analyze |
| model_used | VARCHAR(100) | 使用的模型标识 |
| input_tokens | INT | 输入 token 数 |
| output_tokens | INT | 输出 token 数 |
| cost_usd | FLOAT | 本次调用费用 (美元) |
| duration_ms | INT | 调用耗时 (毫秒) |
| raw_response | JSONB | 原始 API 返回（调试用） |
| status | VARCHAR(20) | 状态: success/failed/timeout |
| error_message | TEXT | 错误信息 |
| created_at | TIMESTAMPTZ | 创建时间 |

#### 表: model_configs (模型配置)

| 字段 | 类型 | 说明 |
|------|------|------|
| id | SERIAL | 主键 |
| stage | VARCHAR(20) | 所属阶段 |
| model_id | VARCHAR(200) | OpenRouter 模型标识 |
| display_name | VARCHAR(100) | 显示名称 |
| is_active | BOOLEAN | 是否启用 |
| max_tokens | INT | 最大输出 token |
| temperature | FLOAT | 温度参数 |
| extra_params | JSONB | 额外参数 |
| created_at | TIMESTAMPTZ | 创建时间 |
| updated_at | TIMESTAMPTZ | 更新时间 |

---

## 5. API 设计

### 5.1 知识条目

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/entries/upload | 上传截图/URL/文本，触发管线 |
| GET | /api/v1/entries | 知识条目列表 (分页/筛选/搜索) |
| GET | /api/v1/entries/{id} | 知识条目详情 (含 MD 内容) |
| PATCH | /api/v1/entries/{id} | 更新条目 (状态/标签/成熟度) |
| DELETE | /api/v1/entries/{id} | 删除条目 (含 MD 文件) |
| GET | /api/v1/entries/{id}/md | 获取原始 MD 文件内容 |
| PUT | /api/v1/entries/{id}/md | 更新 MD 文件内容 |
| POST | /api/v1/entries/{id}/reanalyze | 重新分析 (重跑管线) |

### 5.2 管线控制

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/pipeline/status/{task_id} | 查询管线执行状态 |
| GET | /api/v1/pipeline/logs/{entry_id} | 查看条目的管线日志 |

### 5.3 标签管理

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/tags | 标签列表 (含使用计数) |
| POST | /api/v1/tags | 创建标签 |
| PATCH | /api/v1/tags/{id} | 更新标签 |
| DELETE | /api/v1/tags/{id} | 删除标签 |

### 5.4 用户画像

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/profile | 获取当前活跃画像 |
| PUT | /api/v1/profile | 更新画像 Prompt |

### 5.5 系统配置

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/config/models | 获取模型配置列表 |
| PUT | /api/v1/config/models/{id} | 更新模型配置 |
| GET | /api/v1/stats | 统计数据 (条目数/标签分布/成本统计) |

### 5.6 关键 API 详解

#### POST /api/v1/entries/upload

```json
// Request (multipart/form-data)
{
  "input_type": "screenshot",       // screenshot | url | text
  "file": <binary>,                 // 截图文件 (input_type=screenshot 时)
  "url": "https://...",             // URL (input_type=url 时)
  "text": "...",                    // 文本内容 (input_type=text 时)
  "pipeline_mode": "deep"           // quick | deep
}

// Response 202 Accepted
{
  "task_id": "uuid-xxx",
  "entry_id": "uuid-xxx",
  "status": "processing",
  "message": "Pipeline started in deep mode",
  "estimated_seconds": 45
}
```

#### GET /api/v1/pipeline/status/{task_id}

```json
// Response
{
  "task_id": "uuid-xxx",
  "entry_id": "uuid-xxx",
  "status": "processing",           // queued | processing | completed | failed
  "current_stage": "verify",        // extract | verify | analyze | done
  "stages": {
    "extract": {"status": "completed", "duration_ms": 3200},
    "verify_grok": {"status": "processing", "duration_ms": null},
    "verify_gemini": {"status": "completed", "duration_ms": 5100},
    "analyze": {"status": "pending", "duration_ms": null}
  },
  "total_cost_usd": 0.032
}
```

#### GET /api/v1/entries

```json
// Query Parameters
// ?page=1&per_page=20
// &search=ollama
// &tags=AI,本地部署
// &category=tech
// &maturity=seed,sprouted
// &confidence_min=0.7
// &sort_by=created_at&sort_order=desc

// Response
{
  "items": [
    {
      "id": "uuid-xxx",
      "title": "Ollama - 本地大模型运行框架",
      "category": "tech",
      "confidence": 0.85,
      "maturity": "seed",
      "tags": ["AI", "本地部署", "开源"],
      "actionability": "high",
      "pipeline_mode": "deep",
      "created_at": "2026-03-01T10:00:00Z"
    }
  ],
  "total": 156,
  "page": 1,
  "per_page": 20
}
```

---

## 6. MD 文件规范

### 6.1 文件命名

扁平结构，文件名格式: `{YYYYMMDD}-{slug}.md`

示例: `20260301-ollama-local-llm-framework.md`

### 6.2 Frontmatter 规范

```yaml
---
title: "Ollama - 本地大模型运行框架"
created: 2026-03-01T10:00:00Z
updated: 2026-03-01T10:00:00Z
source_type: screenshot
source_url: null
category: tech
tags:
  - AI
  - 本地部署
  - 开源
  - 视觉模型
confidence: 0.85
maturity: seed
actionability: high
pipeline_mode: deep
related_projects:
  - Nexus EAM
  - Family CFO
review_notes: "Grok 和 Gemini 对社区活跃度的评估存在分歧，建议手动查看 GitHub"
entry_id: "uuid-xxx"
---
```

### 6.3 正文结构

```markdown
## 🔍 这是什么？(定义与本质)

...

## 🛠️ 可以做什么？(核心功能)

...

## 🎯 对我有什么帮助？(个人赋能)

...

## 📦 有什么具体案例？(实战参考)

...

## 🚀 商业场景发散 (降维打击)

...

---

## 📋 验证信息

- **分析模式**: 深度模式
- **可信度**: 0.85
- **社区评价**: 正面
- **最后验证时间**: 2026-03-01
- **审核备注**: Grok 和 Gemini 对社区活跃度的评估存在分歧
```

---

## 7. 前端页面规划

### 7.1 页面列表

| 页面 | 路径 | 功能 |
|------|------|------|
| 上传入口 | / | 截图上传/URL输入/文本粘贴 + 模式选择 |
| 知识列表 | /entries | 搜索、筛选、标签过滤、成熟度过滤 |
| 知识详情 | /entries/:id | MD 渲染 + 状态管理 + 管线日志 |
| 标签管理 | /tags | 标签 CRUD + 使用统计 |
| 个人画像 | /settings/profile | 编辑人格层 Prompt |
| 模型配置 | /settings/models | 管理各阶段模型和参数 |
| 统计面板 | /dashboard | 知识库统计 + 成本统计 |

### 7.2 核心页面描述

#### 上传入口页 (/)

三栏式输入：左侧拖拽上传截图，中间粘贴 URL，右侧文本输入框。底部有"快速模式"/"深度模式"切换开关。提交后显示实时进度条，通过轮询 pipeline status API 更新各阶段状态。

#### 知识列表页 (/entries)

顶部搜索栏 + 标签筛选器（可多选）。左侧边栏显示分类和成熟度过滤器。主区域卡片列表展示知识条目，每张卡片显示标题、标签、confidence 徽章、成熟度状态、创建时间。支持排序（时间/可信度/可操作性）。

#### 知识详情页 (/entries/:id)

左侧主区域渲染 MD 内容（使用 react-markdown）。右侧边栏显示元数据：标签（可编辑）、成熟度（下拉切换）、confidence 分数、管线日志折叠面板（可展开查看每阶段详情和成本）。底部"重新分析"按钮。

---

## 8. 项目结构

```
knowledge-refinery/
├── docker-compose.yml
├── docker-compose.prod.yml          # 生产环境 compose
├── .env.example
├── .gitignore
├── README.md
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic/                     # 数据库迁移
│   │   ├── alembic.ini
│   │   └── versions/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                  # FastAPI 入口
│   │   ├── core/
│   │   │   ├── config.py            # 环境变量 & 配置
│   │   │   ├── database.py          # SQLAlchemy 引擎 & Session
│   │   │   └── pipeline.py          # 管线编排器 (Orchestrator)
│   │   ├── services/
│   │   │   ├── openrouter.py        # OpenRouter 统一调用客户端
│   │   │   ├── extractor.py         # Stage 1: 提纯
│   │   │   ├── verifier.py          # Stage 2: 搜索验证 (Grok + Gemini)
│   │   │   ├── analyzer.py          # Stage 3: 深度分析 (Opus)
│   │   │   ├── md_writer.py         # MD 文件生成 & 管理
│   │   │   ├── preprocessor.py      # 输入预处理 (截图/URL/文本)
│   │   │   └── tag_engine.py        # 标签管理
│   │   ├── models/
│   │   │   ├── entry.py             # KnowledgeEntry 模型
│   │   │   ├── tag.py               # Tag 模型
│   │   │   ├── profile.py           # UserProfile 模型
│   │   │   ├── pipeline_log.py      # PipelineLog 模型
│   │   │   ├── attachment.py        # Attachment 模型
│   │   │   └── model_config.py      # ModelConfig 模型
│   │   ├── schemas/
│   │   │   ├── entry.py             # Pydantic schemas
│   │   │   ├── tag.py
│   │   │   ├── profile.py
│   │   │   └── pipeline.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── entries.py           # 知识条目路由
│   │   │   ├── tags.py              # 标签路由
│   │   │   ├── profile.py           # 画像路由
│   │   │   ├── pipeline.py          # 管线状态路由
│   │   │   ├── config.py            # 配置路由
│   │   │   └── stats.py             # 统计路由
│   │   └── prompts/                 # Prompt 模板 (任务层)
│   │       ├── extraction.txt
│   │       ├── verify_grok.txt
│   │       ├── verify_gemini.txt
│   │       └── analyze.txt
│   └── tests/
│       ├── test_pipeline.py
│       ├── test_openrouter.py
│       └── test_api.py
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── tailwind.config.js
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── api/                     # API 调用层
│       │   └── client.js
│       ├── components/
│       │   ├── layout/
│       │   │   ├── Sidebar.jsx
│       │   │   └── Header.jsx
│       │   ├── upload/
│       │   │   ├── UploadZone.jsx
│       │   │   ├── UrlInput.jsx
│       │   │   ├── TextInput.jsx
│       │   │   └── PipelineProgress.jsx
│       │   ├── entries/
│       │   │   ├── EntryCard.jsx
│       │   │   ├── EntryList.jsx
│       │   │   ├── EntryDetail.jsx
│       │   │   ├── MarkdownRenderer.jsx
│       │   │   └── TagFilter.jsx
│       │   └── settings/
│       │       ├── ProfileEditor.jsx
│       │       └── ModelConfig.jsx
│       ├── pages/
│       │   ├── HomePage.jsx
│       │   ├── EntriesPage.jsx
│       │   ├── EntryDetailPage.jsx
│       │   ├── TagsPage.jsx
│       │   ├── SettingsPage.jsx
│       │   └── DashboardPage.jsx
│       └── hooks/
│           ├── usePipeline.js
│           └── useEntries.js
│
├── knowledge-vault/                 # MD 文件主存储 (Docker volume)
│   └── .gitkeep
│
├── attachments/                     # 上传的截图等附件 (Docker volume)
│   └── .gitkeep
│
└── nginx/
    ├── nginx.conf                   # 本地开发
    └── nginx.prod.conf              # 宝塔生产环境
```

---

## 9. Docker 配置

### 9.1 docker-compose.yml (开发环境)

```yaml
version: "3.8"

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./backend/app:/app/app          # 热重载
      - ./knowledge-vault:/app/knowledge-vault
      - ./attachments:/app/attachments
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    volumes:
      - ./frontend/src:/app/src         # 热重载
    environment:
      - VITE_API_URL=http://localhost:8000

  db:
    image: postgres:16-alpine
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: ${DB_NAME:-knowledge_refinery}
      POSTGRES_USER: ${DB_USER:-refinery}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-refinery_dev_2026}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-refinery}"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  pgdata:
```

### 9.2 .env.example

```bash
# === Database ===
DB_NAME=knowledge_refinery
DB_USER=refinery
DB_PASSWORD=change_me_in_production
DB_HOST=db
DB_PORT=5432

# === OpenRouter ===
OPENROUTER_API_KEY=sk-or-xxxxx
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

# === Model IDs (OpenRouter format) ===
MODEL_EXTRACT=anthropic/claude-3.5-sonnet
MODEL_VERIFY_GROK=x-ai/grok-3
MODEL_VERIFY_GEMINI=google/gemini-2.5-pro
MODEL_ANALYZE=anthropic/claude-opus-4-6

# === Storage ===
KNOWLEDGE_VAULT_PATH=/app/knowledge-vault
ATTACHMENTS_PATH=/app/attachments

# === App ===
APP_ENV=development
APP_SECRET_KEY=change_me
CORS_ORIGINS=http://localhost:3000
```

---

## 10. 降级与容错策略

### 10.1 模型调用降级

```
Stage 2 Grok 失败
  → 只用 Gemini 的验证结果继续
  → 在 pipeline_log 记录 Grok 失败

Stage 2 Gemini 失败
  → 只用 Grok 的验证结果继续

Stage 2 两个都失败
  → 降级为快速模式 (跳过验证，直接进 Stage 3)
  → confidence 自动下调 0.2
  → 在 review_notes 标记"验证阶段失败，结果未经验证"

Stage 3 Opus 失败
  → 重试 1 次
  → 仍然失败 → 用 Sonnet 替代出稿
  → 标记 confidence 为 0.5 以下

Stage 1 Sonnet 失败
  → 整条管线失败
  → 返回错误给前端
  → 保留原始输入，用户可重试
```

### 10.2 成熟度自动流转

```python
# 定时任务 (每天执行一次)
# stale 规则: 超过 90 天未被引用且 maturity != archived
UPDATE knowledge_entries
SET maturity = 'stale', updated_at = NOW()
WHERE maturity IN ('seed', 'sprouted', 'mature')
  AND last_referenced_at < NOW() - INTERVAL '90 days';
```

---

## 11. 开发计划

### Phase 1: 基础框架 (3-4 天)

- Docker Compose 全套搭建
- FastAPI 项目骨架 + PostgreSQL 连接 + Alembic 迁移
- OpenRouter 统一调用客户端
- 前端 React 项目骨架 + 路由 + 布局

### Phase 2: 核心管线 (4-5 天)

- Stage 1 提纯 (Sonnet)
- Stage 2 验证 (Grok + Gemini 并行)
- Stage 3 分析 (Opus)
- 管线编排器 + 异步执行
- MD 文件生成 + Frontmatter
- 管线状态 API + 前端进度展示

### Phase 3: 知识管理 (3-4 天)

- 知识列表页 (搜索/筛选/标签)
- 知识详情页 (MD 渲染 + 元数据)
- 标签管理
- 成熟度状态管理

### Phase 4: 配置与设置 (2-3 天)

- 个人画像编辑器
- 模型配置管理
- 快速/深度模式切换
- 统计面板

### Phase 5: 部署与打磨 (2-3 天)

- 生产环境 Docker Compose
- Nginx 配置 (宝塔)
- 错误处理完善
- Prompt 调优

**总预估: 14-19 天**

---

## 12. V2 版本规划 (后续迭代)

| 功能 | 说明 |
|---|---|
| 知识发酵 | 定时任务，自动交叉分析新旧条目，生成关联报告 |
| 每日简报 | Dashboard 页面，展示知识库健康状态 |
| 语音输入 | 接入 Whisper API 或本地 Whisper，支持语音转文字 |
| Celery 队列 | 替换 BackgroundTasks，支持更大并发 |
| pgvector | 知识条目向量化，支持语义搜索和自动关联 |
| Telegram Bot | 通过 Telegram 直接发截图/链接，触发管线 |
| 批量处理 | 一次上传多张截图，批量进入管线 |
| 导出功能 | 一键导出整个知识库为 Obsidian Vault zip |
