# RAG 企业知识库 - 从 0 到 1 完整构建指南

> 写给自己看的项目手册。覆盖架构思维、代码逻辑、数据流向，读完能独立修改和扩展。

---

## 目录

1. [这个项目是做什么的](#1-这个项目是做什么的)
2. [技术选型：为什么选这些技术](#2-技术选型为什么选这些技术)
3. [整体架构：数据怎么流动](#3-整体架构数据怎么流动)
4. [后端核心链路详解](#4-后端核心链路详解)
   - [配置层：一切从这里开始](#41-配置层-configpy)
   - [数据层：SQLAlchemy 三件套](#42-数据层-databasepy--db_models)
   - [认证层：JWT 令牌体系](#43-认证层-apidepspy)
   - [文档流转：上传 → 入库 → 检索](#44-文档流转上传--入库--检索)
   - [问答链路：从问题到答案](#45-问答链路从问题到答案)
   - [用户体系：注册、登录、权限](#46-用户体系auth_servicepy)
5. [前端核心链路详解](#5-前端核心链路详解)
   - [路由与布局](#51-路由与布局-apptsx--applayouttsx)
   - [认证状态管理](#52-认证状态管理-authstorets)
   - [五个页面逐一看](#53-页面拆解)
6. [关键 Bug 修复记录](#6-关键-bug-修复记录)
7. [开发环境与部署](#7-开发环境与部署)

---

## 1. 这个项目是做什么的

**一句话：** 把企业产品文档（PDF/Word/Markdown）变成可智能问答的知识库。

**三个用户角色：**
- **管理员**：上传产品文档、管理知识库结构、管理用户
- **客户**：只能提问，查阅产品信息
- **系统**：自动解析文档 → 翻译英文 → 向量化 → 存入向量库

**核心场景：** 客户买了一款 MSR165 数据记录仪，不知道怎么安装。打开知识库提问"MSR165 怎么安装"，系统从文档中检索到相关段落，DeepSeek 大模型整理后用中文回答，同时标注信息来源。

**本质：** RAG = Retrieval-Augmented Generation = 检索增强生成。先检索相关文档，再让大模型基于文档回答，而非凭空编造。

---

## 2. 技术选型：为什么选这些技术

| 层 | 技术 | 为什么选它 |
|---|---|---|
| **后端框架** | FastAPI | 异步支持好、自带 Swagger 文档、类型安全 |
| **数据库** | SQLite + SQLAlchemy | 单机部署零配置；ORM 写业务逻辑清晰 |
| **向量库** | ChromaDB | 轻量级、嵌入式、无需单独部署服务 |
| **文档解析** | pdfplumber + python-docx | PDF 文字提取最稳定；DOCX 原生支持 |
| **分块** | LlamaIndex SentenceSplitter | 按句子边界切分，512 字符/块，50 字符重叠 |
| **向量化** | BAAI/bge-large-zh-v1.5 | 中文语义理解最强之一，1024 维向量 |
| **OCR** | RapidOCR | ONNX Runtime 引擎，Windows 免装 CUDA |
| **大模型** | DeepSeek (deepseek-chat) | 中文理解好、API 便宜、OpenAI 兼容 |
| **前端** | React + TypeScript + Ant Design 5 | 类型安全、组件库开箱即用 |
| **翻译** | DeepSeek 自身 | 检测英文文档 → 翻译成中文再入库 |

---

## 3. 整体架构：数据怎么流动

```
                    浏览器（React + Ant Design）
                           │
                    HTTP / WebSocket
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
          /api/auth    /api/documents  /api/chat
          (JWT认证)    (文档上传)      (问答)
              │            │            │
              ▼            ▼            ▼
         auth_service  document_service  chat_service
              │            │            │
              ▼            ▼            ▼
         ┌──────────────────────────────────┐
         │          SQLite 数据库             │
         │  users / products / models /      │
         │  documents / conversations        │
         └──────────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
         文档上传      文档入库       问答检索
              │            │            │
              ▼            ▼            ▼
        文件存储        rag/ingestion.py  rag/retrieval.py
        uploads/       parse → translate  query → embed
                       → chunk → embed    → search ChromaDB
                           │                 │
                           ▼                 ▼
                       ChromaDB           build_prompt()
                      (向量库)            → DeepSeek API
                                             │
                                             ▼
                                        SSE 流式回答
```

**两条核心链路：**

1. **文档入库链路（写）：** 上传文件 → 存磁盘 → 后台任务：解析 → 检测语言 → 英文翻译成中文 → 分块 → BGE 向量化 → 存入 ChromaDB → 更新数据库状态为 ready

2. **问答检索链路（读）：** 用户提问 → BGE 向量化问题 → ChromaDB 搜索 top-5 相似块 → 拼接参考资料 → 发送给 DeepSeek → SSE 流式返回答案 → 保存对话记录

---

## 4. 后端核心链路详解

### 4.1 配置层 `config.py`

**文件定位：** 所有可配置项的中心，用 pydantic-settings 管理，自动从 `.env` 文件读取。

```python
class Settings(BaseSettings):
    # 数据库 —— SQLite 文件路径，支持相对路径自动转绝对
    database_url: str = "sqlite:///./kb.db"

    # JWT —— 令牌签名密钥 + 过期时间
    secret_key: str = "change-me-in-production"
    access_token_expire_minutes: int = 480  # 8小时

    # DeepSeek —— 大模型 API
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # Embedding —— 中文向量模型
    embedding_model: str = "BAAI/bge-large-zh-v1.5"
    embedding_device: str = "cpu"

    # ChromaDB 持久化路径
    chroma_persist_dir: str = "./chroma_data"

    # 文件上传
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 50

    # OCR 开关
    enable_ocr: bool = True
```

**设计要点：**
- `field_validator` 把相对路径转为绝对路径，防止后台任务（工作目录不同）找不到文件 —— 这是踩过的坑
- `.env` 文件通过 `Config.env_file = ".env"` 自动加载，API key 不会写死在代码里

---

### 4.2 数据层 `database.py` + `db_models/`

**`database.py` —— 三行核心代码：**

```python
engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
```

- `check_same_thread: False`：SQLite 默认只允许创建它的线程访问。后台文档处理任务在独立线程跑，不加这个参数会报错。
- `get_db()` 是一个 FastAPI 依赖注入生成器，每个请求获取一个数据库会话，请求结束自动关闭。

**五个数据模型（`db_models/`）：**

| 模型 | 表名 | 核心字段 | 用途 |
|---|---|---|---|
| `User` | users | id, username, password_hash, role | 用户认证 + 权限 |
| `Product` | products | id, name, description | 产品线（如 MSR） |
| `ProductModel` | product_models | id, product_id(FK), name | 产品型号（如 MSR165） |
| `Document` | documents | id, model_id(FK), filename, file_type, file_path, status, chunk_count | 上传的文档 |
| `Conversation` | conversations | id, user_id(FK), question, answer, sources(JSON) | 对话历史 |

**产品-型号-文档的三级结构：**

```
Product (产品线) 1 ──── N ProductModel (型号) 1 ──── N Document (文档)
      MSR                    MSR165                      用户手册.pdf
                             MSR145                      操作说明.docx
```

设计原因：同一个产品可能有多个型号，不同型号有各自的文档。检索时可以限定产品/型号范围。

---

### 4.3 认证层 `api/deps.py`

**两个函数，一个链：**

```python
security = HTTPBearer()                             # 从请求头提取 Bearer token

get_current_user()   # 解码 JWT → 查出 User 对象 → 挂在请求上
      │
      ▼
require_admin()      # 调用 get_current_user → 检查 role == "admin"
```

**JWT 解码流程：**
```
Authorization: Bearer eyJhbG...
     │
     ▼
jwt.decode(token, secret_key) → { "sub": "1", "exp": 1234567890 }
     │
     ▼
db.query(User).filter(User.id == 1).first() → User 对象
```

**安全边界：** 普通 API 只需 `get_current_user`；管理员操作（上传文档、管理用户）加 `require_admin`。在 `api/documents.py` 中可以看到：
- `GET /api/documents/count` → `_=Depends(get_current_user)` — 登录即可
- `POST /api/documents/upload` → `user=Depends(require_admin)` — 必须管理员

---

### 4.4 文档流转：上传 → 入库 → 检索

这是整个系统最核心的链路，涉及 5 个文件协同工作。

#### 第一步：上传（`api/documents.py` + `services/document_service.py`）

```
浏览器选择文件 → POST /api/documents/upload
     │
     ├─ document_service.save_upload_file()
     │   ├─ 检查扩展名（pdf/docx/md/txt）
     │   ├─ UUID 重命名存到 uploads/
     │   └─ 返回 (文件路径, 类型, 大小)
     │
     ├─ document_service.create_document()
     │   └─ 写 SQLite: status="processing"
     │
     └─ bg.add_task(_run_ingestion, doc.id)  ← 后台任务，不阻塞响应
```

**设计要点：** 文档上传后立刻返回（status=processing），真正的解析在后台线程完成。前端轮询 `/api/documents/{id}/status` 直到变为 ready。

#### 第二步：后台入库（`rag/ingestion.py`）

这是最长的函数 `ingest_document()`，分 6 步：

```
1. parse_file(file_path, file_type)      → 提取文本
       ├─ PDF: pdfplumber 逐页提取 + OCR 图片文字
       ├─ DOCX: python-docx 读段落
       └─ MD/TXT: 直接读文件

2. detect_language(text)                 → 判断语言
       └─ CJK 字符占比 > 40% → 中文，否则 → 英文

3. translate_to_chinese(text)            → 仅英文文档执行
       └─ DeepSeek API, temperature=0.1, 保持技术术语

4. SentenceSplitter(chunk_size=512)      → 按句子分块
       └─ 512 字符/块，50 字符重叠（防止关键句被切断）

5. BGE encode → 1024维向量              → 向量化
       └─ SentenceTransformer 模型，CPU 推理

6. ChromaDB collection.add()            → 存入向量库
       └─ 每条 chunk 存: id, embedding, document, metadata
```

**ChromaDB 数据结构：**
```
collection "knowledge_base"
  ├─ id: "doc_5_chunk_0"
  ├─ embedding: [0.023, -0.145, ..., 0.087]  (1024维)
  ├─ document: "MSR165 是一款紧凑型数据记录仪..."
  └─ metadata: {doc_id, filename, product_name, model_name, chunk_index}
```

**关键 Bug 修复：**
- 行 12：必须 `from db_models.user import User`，否则 SQLAlchemy flush 时找不到外键引用的 User 表，抛出 `NoReferencedTableError`，导致文档永久卡在 processing 状态。
- 行 101-105：写前先清理旧 chunks，防止重复 ID 冲突。配合 `delete_document()` 中的 ChromaDB 清理，保证数据一致性。

#### 第三步：检索（`rag/retrieval.py`）

```python
def search(query, product_name="", model_name=""):
    query_embedding = embed_model.encode(query).tolist()    # 问题 → 向量
    results = collection.query(                              # ChromaDB 相似度搜索
        query_embeddings=[query_embedding],
        n_results=5,                                         # 取 top-5
        where={"product_name": product_name} or None         # 可选过滤
    )
    return [{text, filename, product_name, model_name} ...]
```

**相似度搜索原理：** ChromaDB 用余弦距离比较 query 向量和所有 chunk 向量，返回最相似的 5 个。如果选了产品/型号，用 metadata 过滤后再比较。

---

### 4.5 问答链路：从问题到答案

#### 第一步：构建 Prompt（`rag/prompt.py`）

```
参考资料块1: [来源: MSR/MSR165/用户手册.pdf]
MSR165 通过 USB 数据线连接到电脑...

---
参考资料块2: [来源: MSR/MSR165/操作说明.pdf]
双击 install_msr.exe 开始安装...

---
问题: MSR165 怎么安装？

格式要求：用 ## 标题分隔，列表间不空行，关键术语加粗，最后注来源
```

**设计要点：** 系统提示词里包含了「正确示例」，教 DeepSeek 如何排版。中文语义密度高，列表间空行会导致 Markdown 渲染成多个独立 `<ol>`，所以在 prompt 里明确禁止。

#### 第二步：流式调用 DeepSeek（`services/chat_service.py`）

```python
def chat_stream(db, question, user_id, product_id, model_id):
    chunks = search(question, product_name, model_name)   # 检索
    prompt = build_prompt(chunks, question)                # 构建 prompt

    stream = client.chat.completions.create(               # 流式调用
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=2000,
        stream=True
    )

    for chunk in stream:                                   # 逐 token 返回
        yield f"data: {json.dumps(content)}\n\n"           # SSE 格式
```

**为什么流式：** 大模型生成 500 字需要 5-10 秒，不流式用户会以为卡死了。SSE（Server-Sent Events）逐字推送到前端，像 ChatGPT 一样打字效果。

**为什么 JSON 编码：** 之前直接传 `data: {content}\n\n`，但回答内容里有 `\n`（换行符），会把一条消息劈成多行导致前端解析失败。改为 `json.dumps()` 后，换行被转义为 `\n`，前端 `JSON.parse()` 完美还原。

**Markdown 后处理（`_normalize_markdown`）：**
```python
# 标题前补空行
text = re.sub(r"(?<!\n\n)(#{2,3}\s)", r"\n\n\1", text)
# 有序列表项之间删空行（防止渲染成多个 <ol>）
text = re.sub(r"(\d+\.\s.+)\n\n(\d+\.\s)", r"\1\n\2", text)
# 无序列表同理
text = re.sub(r"(-\s.+)\n\n(-\s)", r"\1\n\2", text)
```

#### 第三步：前端渲染（`Chat.tsx`）

前端用 `react-markdown` 的自定义组件渲染 —— 这是 ChatGPT 那种干净排版的关键。

```typescript
// 自定义 h2 样式：大字号 + 底部分隔线
h2: { fontSize: 20, fontWeight: 600, margin: "1.5em 0 0.5em 0",
      paddingBottom: 8, borderBottom: "1px solid #e8e8e8" }

// 自定义 blockquote 样式：灰底 + 左边框（参考来源用）
blockquote: { margin: "1em 0", padding: "8px 16px",
              borderLeft: "3px solid #d0d0d0", color: "#555",
              background: "#fafafa" }
```

**SSE 解析（前端）：**
```typescript
const reader = res.body?.getReader();
while (reader) {
    const { done, value } = await reader.read();
    const text = decoder.decode(value, { stream: true });
    for (const line of text.split("\n")) {
        if (line.startsWith("data: ")) {
            const raw = line.slice(6);         // 去掉 "data: " 前缀
            if (raw === "[DONE]") break;        // 结束标记
            answer += JSON.parse(raw);           // JSON 解码
        }
    }
}
```

---

### 4.6 用户体系 `services/auth_service.py`

**注册流程：**
```
用户名/密码 → 校验格式 → bcrypt 哈希 → 写入 users 表
```

**登录流程：**
```
用户名/密码 → 查出用户 → bcrypt 验证 → 生成 JWT → 返回 token
```

**JWT payload：**
```json
{
  "sub": "1",           // 用户 ID
  "exp": 1234567890     // 过期时间 = 当前时间 + 480 分钟
}
```

**首次启动自动创建管理员：** `seed_admin.py` 在 `lifespan` 启动阶段执行，检查 users 表是否为空，为空则创建 admin/admin。

---

## 5. 前端核心链路详解

### 5.1 路由与布局 `App.tsx` + `AppLayout.tsx`

**路由守卫：**
```
/              → <Protected> → 检查 token → 有则渲染 AppLayout，无则跳转 /login
/login         → Login 页面（公开）
/knowledge     → KnowledgeBase（管理员才可见菜单项）
/chat          → ChatPage
/users         → UserManagement（管理员才可见）
```

**AppLayout 结构：**
```
┌──────────┬──────────────────────────────────────┐
│ Sidebar  │ Header: 用户名(角色) | 退出按钮        │
│          ├──────────────────────────────────────┤
│ 首页      │                                      │
│ 知识库    │         <Outlet />                   │
│ 问答      │     (子路由内容渲染在这里)              │
│ 用户管理  │                                      │
└──────────┴──────────────────────────────────────┘
```

**权限控制：** 菜单项根据 `role` 动态生成 —— `role === "admin"` 才显示「知识库」和「用户管理」。

### 5.2 认证状态管理 `authStore.ts`

```typescript
const { role, username, logout } = useAuthStore();

// 登录时：存 token 到 localStorage + 解析 JWT 获取 role/username
// 退出时：清除 localStorage + 重置状态
// 刷新页面：从 localStorage 恢复 token
```

**token 怎么带在请求上：** `api/client.ts` 的 axios 拦截器自动在每个请求头注入 `Authorization: Bearer <token>`。401 响应自动清除 token 并跳转登录页。

### 5.3 页面拆解

**Login 页面：** 标准登录表单，调用 `/api/auth/login`，成功后存 token 并跳转首页。

**Dashboard 页面：** 三个统计卡片（产品数/文档数/今日问答），点击可跳转。

**KnowledgeBase 页面（管理员核心操作页）：**
```
三栏布局：
  产品列表         型号列表         文档列表
  ┌────────┐    ┌────────┐    ┌────────┐
  │ MSR    │ →  │ MSR165 │ →  │ 手册.pdf │ [就绪] [删除]
  │ (新增) │    │ (新增) │    │ 说明.docx│ [处理中]
  └────────┘    └────────┘    │ (上传)   │
                              └────────┘
```
- 上传自动触发 `handleUpload()`，FormData 方式提交
- 文档状态为 processing 时，每 3 秒轮询状态直到 ready
- 删除文档同步清理文件 + ChromaDB 向量

**ChatPage 页面：**
```
┌──────────────┬──────────────────────────────┐
│ 侧边栏 260px │      聊天区域                  │
│              │                              │
│ [+ 新对话]   │   产品选择  型号选择            │
│              │                              │
│ 历史对话1     │   ┌──────────────────┐       │
│ 历史对话2 ✕   │   │ 用户问题气泡       │       │
│ 历史对话3     │   └──────────────────┘       │
│              │   ┌──────────────────┐       │
│              │   │ AI回答(Markdown)  │       │
│              │   │ > 参考来源 tags   │       │
│              │   └──────────────────┘       │
│              │                              │
│              │  [输入框]          [发送]     │
└──────────────┴──────────────────────────────┘
```
- 历史对话：点击可查看，右上角 X 可删除（同步删数据库）
- 时间显示：按日历日期计算「今天/昨天/N天前」
- 时区修正：数据库存 UTC，前端加 `Z` 后缀解析为 UTC 再转本地时间

**UserManagement 页面：** 用户表格 + 新增/删除/修改角色。只对管理员可见。

---

## 6. 关键 Bug 修复记录

这是从开发过程中踩过的坑，每个都花了不少时间排查：

| 问题 | 根因 | 修复 |
|---|---|---|
| 文档永久停在 processing | `ingestion.py` 未 import User 模型，FK 解析失败，commit 报错 | 添加 `from db_models.user import User` |
| PaddleOCR Windows 崩溃 | oneDNN / PIR API 兼容性问题 | 换 RapidOCR（ONNX Runtime） |
| SSE 回答换行丢失 | 原始 `data: {content}\n\n` 格式，内容中的 `\n` 破坏协议 | JSON 编码：`json.dumps(content)` |
| Markdown 列表渲染成多个 `<ol>` | 列表项之间的空行被 Markdown 解析为独立列表 | `_normalize_markdown` 移除列表间空行 |
| 仪表盘文档数为 0 | Dashboard 未调 API，hardcode 为 0 | 新增 `GET /api/documents/count` 端点 |
| 仪表盘文档数显示 9 实际只有 4 | 手动删 SQLite 时未清理 ChromaDB，旧向量残留 | 删除文档时同步删 ChromaDB chunk |
| 历史对话时间差 8 小时 | 数据库存 UTC，前端当本地时间解析 | `new Date(dt + "Z")` 标明 UTC |
| 英文文档搜不到 | bge-large-zh-v1.5 对英文向量表征弱 | upload 时自动检测英文 → DeepSeek 翻译 → 中文入库 |
| 启动脚本中文乱码 | cmd 编码 GBK vs 文件 UTF-8 | 去中文全用英文 + `chcp 65001` |
| 二次启动端口占用 | 上次关闭窗口后进程残留 | `for /f ... netstat` 启动前杀旧进程 |

---

## 7. 开发环境与部署

### 本地开发

```bash
# 后端
cd backend
conda activate rag
uvicorn main:app --host 0.0.0.0 --port 8000

# 前端（开发模式，热更新）
cd frontend
npm run dev
```

### 一键启动

```bash
# 日常使用
双击 start.bat  → 后端 8000 端口 + 自动打开浏览器

# 改前端代码时
双击 dev.bat    → 后端 8000 + 前端 5173（热更新）
```

### 生产部署（局域网）

```bash
# 1. 构建前端
cd frontend && npm run build

# 2. 启动（后端 serve 前端，只需一个端口）
cd backend && uvicorn main:app --host 0.0.0.0 --port 8000

# 3. 团队成员访问
http://<你的IP>:8000
```

### 云部署（待实施）

当前代码已做好云部署准备：API 地址为相对路径，后端内置前端静态文件服务。搬到云服务器后只需启动后端即可。

---

> **下一步：** 了解完整体架构后，可以从 `rag/ingestion.py` 的 `ingest_document()` 函数开始深入，它是整个系统最核心的链路，涵盖了解析、翻译、分块、向量化、存储的全过程。然后看 `services/chat_service.py` 的 `chat_stream()`，理解检索 + 生成是如何串联的。
