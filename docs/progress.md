# 企业知识库 — 开发进度记录

> 项目路径: `D:\RAG`
> 开始时间: 2026-05-14
> 技术栈: FastAPI + React/TypeScript + Ant Design 5 + ChromaDB + LlamaIndex + DeepSeek

---

## 进度总览

| Task | 名称 | 状态 | 完成时间 |
|------|------|------|----------|
| 1 | 后端项目脚手架 | ✅ | 2026-05-14 |
| 2 | 数据库模型 | ✅ | 2026-05-14 |
| 3 | 认证模块 | ✅ | 2026-05-14 |
| 4 | 产品管理 API | ✅ | 2026-05-14 |
| 5 | 型号管理 API | ✅ | 2026-05-14 |
| 6 | 文档上传与处理 API | ✅ | 2026-05-14 |
| 7 | RAG Pipeline | ✅ | 2026-05-14 |
| 8 | 问答 API | ✅ | 2026-05-14 |
| 9 | 用户管理 API | ✅ | 2026-05-14 |
| 10 | 前端项目脚手架 | ✅ | 2026-05-14 |
| 11 | 登录页 + 布局 | ✅ | 2026-05-14 |
| 12 | 首页 Dashboard | ✅ | 2026-05-14 |
| 13 | 知识库管理页 | ✅ | 2026-05-14 |
| 14 | 问答页 | ✅ | 2026-05-14 |
| 15 | 用户管理页 | ✅ | 2026-05-14 |
| 16 | 集成测试 | ✅ | 2026-05-14 |
| 17 | 用户名/密码格式校验 | ✅ | 2026-05-14 |
| 18 | 修复文档向量化失败问题 | ✅ | 2026-05-14 |
| 19 | PDF 图片 OCR 文字提取 | ✅ | 2026-05-14 |

---

## 验证结果

**后端测试：** 8/8 全部通过
- test_health ✅
- test_register_requires_admin ✅
- test_login_invalid_user ✅
- test_chat_requires_auth ✅
- test_conversations_requires_auth ✅
- test_list_docs_requires_auth ✅
- test_get_products_requires_auth ✅
- test_create_product_requires_admin ✅

**前端验证：**
- TypeScript 类型检查：零错误
- 生产构建：成功（855ms）
- 页面清单：登录页 / 首页 / 知识库 / 问答 / 用户管理

**项目文件统计：**
- `backend/` — 25 个 Python 文件（config, database, main, 5 models, 5 schemas, 5 services, 5 API routers, 4 RAG modules, 4 tests）
- `frontend/` — Vite + React + TypeScript + Ant Design 5（5 pages, 2 stores, 1 API client, types）
- `docs/` — 设计文档 + 实施计划 + 进度记录

---

## 启动方式

```bash
# 1. 启动后端
cd D:\RAG\backend
conda activate rag
uvicorn main:app --reload --port 8000

# 2. 启动前端（新终端）
cd D:\RAG\frontend
npm run dev

# 3. 访问 http://localhost:5173
```

**首次使用：** 先通过 API 注册 admin 账号，然后用 admin 创建产品和客户账号。

---

## 使用流程

### 第一步：创建管理员账号

运行 `python seed_admin.py`，创建初始管理员（用户名和密码均为字母/数字/下划线，3-50 字符）。

### 第二步：登录系统

浏览器打开 `http://localhost:5173`，使用管理员账号登录。

### 第三步：创建产品

进入「知识库」页面，在最左侧「产品」栏点击「+ 新增」，输入产品名称（如「智能传感器」）。

### 第四步：创建型号

选中产品后，在中间栏「型号」点击「+ 新增」，输入型号名称（如「X200-Pro」）。

### 第五步：上传文档

选中型号后，在右侧栏「文档」点击「上传」，选择 PDF/Word/Markdown 文件。上传后文档状态显示「处理中」→「就绪」，表示向量化完成。

### 第六步：开始问答

进入「问答」页面，可选择按产品/型号过滤知识范围，输入问题后发送。系统通过 RAG 检索相关文档片段，由 DeepSeek 生成回答并附上引用来源。

### 第七步：管理用户

进入「用户管理」页面（仅管理员），可查看所有用户并修改角色。通过 `POST /api/auth/register`（管理员权限）创建新用户账号分发给客户。

---

## Task 17: 用户名/密码格式校验 ✅

**完成内容：**

**后端（schemas/auth.py）：**
- `RegisterRequest.username` 增加 Field 约束：`min_length=3`, `max_length=50`, `pattern=r"^[a-zA-Z0-9_]+$"`
- `RegisterRequest.password` 增加 Field 约束：`min_length=6`, `max_length=128`
- Pydantic 自动校验并返回中文错误提示

**后端（services/auth_service.py）：**
- `register()` 函数增加服务端二次校验：用户名长度、字符白名单、密码长度
- 所有校验失败返回 400 + 中文错误消息

**前端（Login.tsx）：**
- 用户名字段增加校验规则：正则匹配字母/数字/下划线 + 最少 3 字符
- 密码字段增加校验规则：最少 6 字符
- 每个字段下方显示 `extra` 格式提示文字

**规则总结：**
- 用户名：3-50 个字符，仅支持 `a-z`、`A-Z`、`0-9`、`_`
- 密码：6-128 个字符

**测试结果：** 8/8 后端测试全部通过，前端 TypeScript 零错误，生产构建成功。

---

## Task 1: 后端项目脚手架 ✅

**完成内容：**
- `backend/config.py` — pydantic-settings 配置，含数据库/JWT/DeepSeek/Embedding/ChromaDB/上传等全部配置项
- `backend/database.py` — SQLAlchemy 引擎 + Session + Base + get_db 依赖注入
- `backend/main.py` — FastAPI 应用，lifespan 自动建表，CORS localhost:5173，/api/health 健康检查
- `backend/.env` — 环境变量模板

**测试结果：** uvicorn 启动正常，/api/health → `{"status":"ok"}`，Swagger /docs 可访问，kb.db 自动生成

---

## Task 2: 数据库模型 ✅

**完成内容：**
- `db_models/user.py` — User 模型（users 表）
- `db_models/product.py` — Product 模型（products 表）
- `db_models/product_model.py` — ProductModel 模型（product_models 表）
- `db_models/document.py` — Document 模型（documents 表）
- `db_models/conversation.py` — Conversation 模型（conversations 表）

**测试结果：** 5 张表全部创建成功，外键关系正确，SQLite 验证通过

---

## Task 3: 认证模块 ✅

**完成内容：**
- `schemas/auth.py` — LoginRequest, RegisterRequest, TokenResponse
- `services/auth_service.py` — bcrypt 密码哈希, JWT 令牌生成, 认证/注册逻辑
- `api/deps.py` — get_current_user (Bearer Token 解析), require_admin (管理员守卫)
- `api/auth.py` — POST /api/auth/login, POST /api/auth/register
- `tests/test_auth.py` — 3 个测试用例

**测试结果：** 3/3 测试通过。注册需 admin 权限校验正常，无效用户拒绝登录。

---

## Task 18: 修复文档向量化失败问题 ✅

**问题：** 上传 PDF 文档后一直显示「处理中」，不会自动变为「就绪」。

**根因分析（3 层）：**

1. **SQLAlchemy FK 解析失败（直接原因）：** `rag/ingestion.py` 未导入 `User` 模型。当后台任务调用 `db.commit()` 提交 Document 状态变更时，SQLAlchemy 需要解析 `documents.uploaded_by → users.id` 外键关系。由于 `User` 模型未在当前模块导入，其表元数据未注册到 SQLAlchemy mapper 中，抛出 `NoReferencedTableError`。

2. **错误处理二次崩溃（隐蔽原因）：** `ingest_document` 的 `except` 块尝试 `db.commit()` 设置 error 状态，但此时 session 已因第一次 flush 失败进入 "pending rollback" 状态，导致 `PendingRollbackError`，error 状态也无法写入。文档永远停留在 "processing"。

3. **错误完全不可见（运维原因）：** `_run_ingestion` 没有 `except` 块，也没有 `logging` 或 `print`。后台线程中的异常被静默吞掉，控制台看不到任何错误输出。

**修复内容：**

| 文件 | 修改 | 目的 |
|------|------|------|
| `rag/ingestion.py` | 导入 `User` 模型 | 确保 FK 解析时表元数据已注册 |
| `rag/ingestion.py` | except 块先 `db.rollback()` 再 `db.commit()` | 解决 session 状态冲突 |
| `rag/ingestion.py` | 添加 `logging` | 记录解析/分块/入库/错误全流程 |
| `api/documents.py` | `_run_ingestion` 添加异常捕获和 logger | 后台错误不再静默 |
| `api/documents.py` | 异常时额外确保 doc.status="error" | 状态兜底更新 |
| `main.py` | lifespan 预加载 Embedding 模型 | 启动时即加载，消除首次请求延迟 |
| `config.py` | 数据库/chroma/upload 路径解析为绝对路径 | 避免工作目录差异导致路径不一致 |

**测试结果：** 8/8 后端测试通过，TypeScript 零错误，3 个已上传 PDF 均显示 "ready"（分别 20/4/2 chunks）。

---

## Task 19: PDF 图片 OCR 文字提取 ✅

**问题：** PDF 中的图片（示意图、截图、带标注的图表）含有的文字信息在向量化时被完全丢弃，`pdfplumber.extract_text()` 只能提取 PDF 文本流中的文字。

**方案：** 方案 A（OCR）——用 RapidOCR 将每页渲染为图片后识别图中文字，与正文合并入库。

**为什么选 RapidOCR 而不是 PaddleOCR：**
- PaddlePaddle 3.3.1 在 Windows 上有 oneDNN 底层 bug，OCR 推理直接崩溃（`NotImplementedError`）
- RapidOCR 使用 ONNX Runtime（环境已有），模型架构与 PaddleOCR 相同（PP-OCRv5），精度持平，无需 PaddlePaddle

**实现文件：**

| 文件 | 修改 |
|------|------|
| `rag/ocr.py` | **新建** — RapidOCR 单例模块，`get_ocr_reader()` 懒加载，`ocr_page_image()` 识别单页图片并返回文字 |
| `rag/ingestion.py` `parse_file()` | PDF 分支增加 OCR：每页渲染 200dpi 图片 → RapidOCR 识别 → 合并入 text |
| `config.py` | 新增 `enable_ocr: bool = True`，可关闭 OCR 以加快处理速度 |

**耗时实测：**
- 不开启 OCR：22 页 PDF ≈ 3 秒
- 开启 OCR：22 页 PDF ≈ 112 秒（约 5 秒/页）
- 单页 OCR 平均识别 800-900 字符图片文字

**测试结果：** 8/8 后端测试通过，前端构建成功。12 页 PDF 完整入库（解析 → OCR → 切片 → 向量化 → ChromaDB），状态 "ready"，20 chunks。

---

