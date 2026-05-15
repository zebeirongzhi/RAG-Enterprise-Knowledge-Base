# 企业知识库系统 — 设计文档

> 项目路径: `D:\RAG`
> 更新日期: 2026-05-14

---

## 1. 项目概述

基于 RAG（检索增强生成）构建企业知识库，大模型接入 DeepSeek 官方 API。核心功能：产品手册的层级管理、智能问答。

---

## 2. 技术选型

| 维度 | 选择 | 说明 |
|------|------|------|
| 架构模式 | 前后端分离 | FastAPI + React/TypeScript |
| 前端框架 | React + TypeScript | 生态最大 |
| UI 组件库 | Ant Design 5 | 国内企业级场景最成熟 |
| 后端框架 | FastAPI | 异步支持好，API 文档自动生成 |
| 大模型 | DeepSeek 官方 API | 按量付费 |
| Embedding | BGE-large-zh (BAAI) | 中文效果最好的开源模型之一 |
| 向量数据库 | ChromaDB | 轻量零配置，适合当前规模 |
| RAG 框架 | LlamaIndex | 层级索引匹配"产品→型号→文档"结构 |
| 数据库 | SQLite（开发）/ PostgreSQL 预留 | |
| 部署 | 本地开发，Docker 预留 | |

---

## 3. 用户角色与权限

| 角色 | 权限 |
|------|------|
| 内部管理员 (admin) | 管理知识库、上传/删除文档、管理用户、查看全部对话 |
| 外部客户 (customer) | 仅提问，查看自己的对话历史 |

---

## 4. 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                  前端 (React + Ant Design 5)              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │ 知识库管理 │  │ 文档上传  │  │ 智能问答  │  │ 用户管理  │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
└──────────────────────┬──────────────────────────────────┘
                       │ REST API (JWT Auth)
┌──────────────────────┴──────────────────────────────────┐
│                  后端 (FastAPI)                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────┐   │
│  │ 用户模块  │  │ 文档模块  │  │     RAG 问答模块      │   │
│  │ 登录/权限 │  │ 上传/解析 │  │ 检索 → Prompt → LLM   │   │
│  └──────────┘  └────┬─────┘  └──────────┬───────────┘   │
│                     │                    │                │
│              ┌──────┴──────┐    ┌───────┴────────┐       │
│              │  LlamaIndex  │    │ ChromaDB       │       │
│              │  文档索引编排  │    │ 向量存储+元数据  │       │
│              └──────┬──────┘    └────────────────┘       │
│                     │                                    │
│              ┌──────┴──────┐                             │
│              │ BGE Embedding│                             │
│              │ 本地向量化    │                             │
│              └─────────────┘                             │
└──────────────────────────────────────────────────────────┘
```

### 数据流（用户提问）

```
用户提问 → /api/chat → Embedding转向量 → ChromaDB检索Top-K
    → 元数据过滤(产品/型号) → 构建Prompt(上下文+问题)
    → DeepSeek API → 流式返回答案 → 前端渲染
```

---

## 5. 项目目录结构

```
D:\RAG\
├── frontend/          # React + TypeScript + Ant Design 5
│   ├── src/
│   │   ├── pages/     # 登录、知识库管理、问答、用户管理
│   │   ├── components/ # 通用组件
│   │   ├── api/       # 后端请求封装
│   │   └── stores/    # 状态管理 (Zustand)
│   └── ...
├── backend/           # FastAPI
│   ├── api/           # 路由 (auth, documents, chat, admin)
│   ├── core/          # 配置、依赖注入
│   ├── models/        # 数据库模型 (SQLite)
│   ├── services/      # 业务逻辑 (rag_service, doc_service)
│   ├── rag/           # RAG 核心 (LlamaIndex pipeline)
│   └── ...
└── docs/              # 设计文档 + 开发进度
    └── design.md
```

---

## 6. 数据库模型

```sql
-- 用户表
users (id, username, password_hash, role [admin|customer], created_at)

-- 产品线
products (id, name, description, created_by, created_at)

-- 产品型号
models (id, product_id FK, name, description, created_at)

-- 文档
documents (
  id, model_id FK, filename, file_type [pdf|docx|md],
  file_path, file_size, status [processing|ready|error],
  chunk_count, uploaded_by, created_at
)

-- 对话历史
conversations (
  id, user_id FK, question, answer, sources JSON,
  product_id FK nullable, model_id FK nullable, created_at
)
```

**设计要点：**
- documents 挂在 models 下，实现"产品 → 型号 → 文档"三级层级
- status 字段追踪文档处理状态（上传 → 解析 → 切片 → 向量化 → 就绪）
- conversations.sources 存引用来源，回答时展示"出自哪个文档"
- 开发阶段用 SQLite，预留 PostgreSQL 切换接口

---

## 7. API 接口

```
POST   /api/auth/login              # 登录，返回 JWT
POST   /api/auth/register           # 注册 (admin only)

GET    /api/products                # 产品列表
POST   /api/products                # 创建产品 (admin)
PUT    /api/products/{id}           # 编辑产品 (admin)
DELETE /api/products/{id}           # 删除产品 (admin)

GET    /api/products/{id}/models    # 型号列表
POST   /api/models                  # 创建型号 (admin)
DELETE /api/models/{id}             # 删除型号 (admin)

GET    /api/models/{id}/docs        # 文档列表
POST   /api/documents/upload        # 上传文档 (admin)，异步处理
DELETE /api/documents/{id}          # 删除文档及向量 (admin)
GET    /api/documents/{id}/status   # 查询处理状态

POST   /api/chat/ask                # 提问（可指定 product_id/model_id）
POST   /api/chat/stream             # 流式提问 (SSE)

GET    /api/conversations           # 对话历史
GET    /api/users                   # 用户管理 (admin)
PUT    /api/users/{id}              # 修改角色 (admin)
```

**设计要点：**
- /api/chat/ask 支持传 product_id 或 model_id，限定检索范围提高准确率
- 流式接口用 SSE，DeepSeek 支持流式返回
- 文档上传后异步处理，前端轮询 status 接口

---

## 8. RAG Pipeline 详细设计

### 处理流程

```
文档上传 → 文件解析 → 文本切片 → BGE向量化 → ChromaDB存储
                                                    ↓
用户提问 → BGE转向量 → ChromaDB检索(元数据过滤) → Top-K
                                                    ↓
构建Prompt(系统指令+检索内容+问题) → DeepSeek API → 流式返回
```

### 各阶段工具

| 阶段 | 工具 | 说明 |
|------|------|------|
| PDF解析 | pdfplumber / PyMuPDF | 提取文本+表格，保留结构 |
| Word解析 | python-docx | 提取段落+表格 |
| Markdown解析 | Python 原生 | 按标题层级拆分 |
| 文本切片 | LlamaIndex SentenceSplitter | chunk_size=512, overlap=50 |
| 向量化 | BAAI/bge-large-zh-v1.5 | 本地 sentence-transformers 加载 |
| 存储 | ChromaDB | 每向量附带元数据：product_name, model_name, doc_id, chunk_index |

### 元数据过滤检索

| 限定方式 | 检索范围 |
|----------|----------|
| 不限定 | 全库检索 Top-5 |
| 限定产品 | product_name = "XX"，仅该产品下 |
| 限定型号 | model_name = "XX-YY"，仅该型号下 |

### Prompt 模板

```
你是一个企业知识库助手。基于以下参考资料回答用户问题。
如果参考资料不足以回答问题，请如实告知，不要编造。

参考资料：
{retrieved_context}

用户问题：{question}

要求：
1. 回答准确，引用具体文档来源
2. 如涉及多份资料，综合回答
3. 给出具体的操作步骤（如适用）
```

---

## 9. 前端页面设计

### 布局结构（Ant Design Pro 风格）

```
┌──────────────────────────────────────────────────────┐
│  Logo  企业知识库     [产品切换 Select]   🔔  👤 退出  │  ← Header
├──────────┬───────────────────────────────────────────┤
│  📊 首页  │                                          │
│  📁 知识库 │    主内容区                               │
│  💬 问答  │                                          │
│  👥 用户  │                                          │
│  ⚙️ 设置  │                                          │
├──────────┴───────────────────────────────────────────┤
│  Sider (admin 可见全部菜单, customer 仅首页+问答)        │
└──────────────────────────────────────────────────────┘
```

### 页面清单

**1. 登录页** — 简洁居中卡片，Logo + 表单 + 深色渐变背景

**2. 首页 Dashboard** — 统计卡片（产品数/文档数/今日问答数）+ 快速入口

**3. 知识库管理页**（admin only）— 三栏级联布局：
- 左栏：产品列表，支持新增/编辑/删除
- 中栏：型号列表，随产品选择联动
- 右栏：文档列表，显示文件名、类型、处理状态，支持上传/删除

**4. 问答页** — 类 ChatGPT 聊天界面：
- 顶部：产品/型号下拉选择器，限定检索范围
- 中间：对话区，流式渲染，每条回答标注引用来源
- 底部：输入区 + 发送按钮

**5. 用户管理页**（admin only）— Table 展示：用户名/角色/创建时间/操作

---

## 10. 错误处理策略

### 后端

| 场景 | HTTP | 处理方式 |
|------|------|----------|
| DeepSeek API 超时/不可用 | 503 | "AI 服务暂时不可用，请稍后重试"，前端显示重试按钮 |
| 文档解析失败 | 400 | status → error，返回具体原因 |
| Embedding 模型未加载 | — | FastAPI startup 检查，失败阻止启动 |
| 文件上传过大 (>50MB) | 413 | 中间件拦截 |
| JWT 过期/无效 | 401 | 前端自动跳转登录页 |
| 权限不足 | 403 | 明确提示当前角色限制 |
| 数据库操作失败 | 500 | 详细日志记录，前端不暴露细节 |
| 资源不存在 | 404 | 标准 NotFound |

### 前端

| 场景 | 处理方式 |
|------|----------|
| API 请求失败 | axios 拦截器统一处理，message.error 提示 |
| 文件上传进度 | Ant Design Upload 组件进度条 |
| 文档处理中 | status badge (processing=蓝色转圈/ready=绿色/error=红色) |
| 网络断开 | 全局提示，恢复后自动重连 |
| 表单校验 | Ant Form rules + 后端双重校验 |

### 全局兜底

FastAPI 全局异常处理器，捕获未处理异常 → 500 + 日志记录。

---

## 11. 测试策略

| 层级 | 工具 | 范围 |
|------|------|------|
| 后端单元测试 | pytest | services、rag 模块核心逻辑 |
| API 集成测试 | pytest + httpx | 所有 API 端点，含权限校验 |
| RAG 质量测试 | 手工构建测试集 | 10-20 个典型问题，验证检索+回答质量 |
| 前端组件测试 | Vitest + React Testing Library | 关键组件渲染和交互 |
| E2E 测试 | Playwright（可选） | 核心流程：登录→上传→提问 |

### 测试重点

- 权限边界：admin 操作 customer 不可访问
- 文档处理：正常文档 / 空文件 / 损坏文件 / 超大文件
- RAG 召回：相同问题有没有召回正确文档
- 流式响应：SSE 中断、超时场景

---

## 待补充章节

（设计完成，等待整体确认后转入开发计划）
