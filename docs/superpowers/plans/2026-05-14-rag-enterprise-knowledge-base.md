# 企业知识库系统 — 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 基于 RAG 构建企业知识库，支持产品手册层级管理（产品→型号→文档）和智能问答，DeepSeek 作为大模型后端。

**Architecture:** FastAPI 后端 + React/TypeScript 前端，ChromaDB 向量存储，LlamaIndex 编排 RAG Pipeline，BGE-large-zh 本地 Embedding，JWT 双角色权限。

**Tech Stack:** Python 3.10+ / FastAPI / SQLAlchemy / ChromaDB / LlamaIndex / BGE / React 18 / TypeScript / Ant Design 5 / Zustand

**环境:** 虚拟环境 `anaconda3/envs/rag`，项目路径 `D:\RAG`

---

## 文件结构

```
D:\RAG\
├── backend/
│   ├── main.py              # FastAPI 入口，启动事件
│   ├── config.py             # pydantic-settings 配置
│   ├── database.py           # SQLAlchemy engine + session
│   ├── api/
│   │   ├── deps.py           # 依赖注入 (get_db, get_current_user)
│   │   ├── auth.py           # 登录/注册路由
│   │   ├── products.py       # 产品 CRUD 路由
│   │   ├── product_models.py # 型号 CRUD 路由
│   │   ├── documents.py      # 文档上传/管理路由
│   │   ├── chat.py           # 问答路由 (含 SSE)
│   │   └── users.py          # 用户管理路由
│   ├── db_models/
│   │   ├── user.py
│   │   ├── product.py
│   │   ├── product_model.py
│   │   ├── document.py
│   │   └── conversation.py
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── product.py
│   │   ├── product_model.py
│   │   ├── document.py
│   │   └── chat.py
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── product_service.py
│   │   ├── model_service.py
│   │   ├── document_service.py
│   │   ├── chat_service.py
│   │   └── user_service.py
│   ├── rag/
│   │   ├── embeddings.py     # BGE 模型加载
│   │   ├── ingestion.py      # 文档解析 → 切片 → 向量化 → 入库
│   │   ├── retrieval.py      # 查询 → 向量检索
│   │   └── prompt.py         # Prompt 模板构建
│   └── tests/
│       ├── test_auth.py
│       ├── test_products.py
│       ├── test_documents.py
│       └── test_chat.py
├── frontend/
│   ├── src/
│   │   ├── main.tsx          # React 入口
│   │   ├── App.tsx           # 路由配置
│   │   ├── api/
│   │   │   └── client.ts     # axios 实例 + 拦截器
│   │   ├── stores/
│   │   │   └── authStore.ts  # Zustand 认证状态
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── KnowledgeBase.tsx
│   │   │   ├── Chat.tsx
│   │   │   └── UserManagement.tsx
│   │   ├── components/
│   │   │   └── AppLayout.tsx # 全局布局
│   │   └── types/
│   │       └── index.ts
│   └── ...
└── docs/
    ├── design.md
    ├── progress.md           # 开发进度记录
    └── superpowers/
        └── plans/
            └── 2026-05-14-rag-enterprise-knowledge-base.md
```

---

### Task 1: 后端项目脚手架

**Files:**
- Create: `backend/config.py`
- Create: `backend/database.py`
- Create: `backend/main.py`

- [ ] **Step 1: 创建配置文件**

```python
# backend/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 数据库
    database_url: str = "sqlite:///./kb.db"

    # JWT
    secret_key: str = "change-me-in-production-use-a-strong-random-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    # DeepSeek
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # Embedding
    embedding_model: str = "BAAI/bge-large-zh-v1.5"
    embedding_device: str = "cpu"

    # ChromaDB
    chroma_persist_dir: str = "./chroma_data"

    # Upload
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 50

    class Config:
        env_file = ".env"

settings = Settings()
```

- [ ] **Step 2: 创建数据库连接**

```python
# backend/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},  # SQLite 需要
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 3: 创建 FastAPI 入口**

```python
# backend/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时创建表
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="企业知识库 API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 4: 测试启动**

```bash
cd D:\RAG\backend
conda activate rag
uvicorn main:app --reload --port 8000
```

打开 `http://localhost:8000/docs` 确认 Swagger 文档可见。
`GET /api/health` 返回 `{"status": "ok"}`。

- [ ] **Step 5: 创建 .env 文件**

```bash
# backend/.env
DEEPSEEK_API_KEY=your-api-key-here
SECRET_KEY=your-secret-key-change-me
```

验证：重启 uvicorn，确认启动无报错。

---

### Task 2: 数据库模型（SQLAlchemy ORM）

**Files:**
- Create: `backend/db_models/__init__.py`
- Create: `backend/db_models/user.py`
- Create: `backend/db_models/product.py`
- Create: `backend/db_models/product_model.py`
- Create: `backend/db_models/document.py`
- Create: `backend/db_models/conversation.py`

- [ ] **Step 1: 创建 User 模型**

```python
# backend/db_models/user.py
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="customer")  # admin | customer
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

- [ ] **Step 2: 创建 Product 模型**

```python
# backend/db_models/product.py
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), default="")
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

- [ ] **Step 3: 创建 ProductModel 模型**

```python
# backend/db_models/product_model.py
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

class ProductModel(Base):
    __tablename__ = "product_models"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

- [ ] **Step 4: 创建 Document 模型**

```python
# backend/db_models/document.py
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("product_models.id", ondelete="CASCADE"), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)  # pdf, docx, md
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="processing")  # processing, ready, error
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

- [ ] **Step 5: 创建 Conversation 模型**

```python
# backend/db_models/conversation.py
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from database import Base

class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    question: Mapped[str] = mapped_column(String(2000), nullable=False)
    answer: Mapped[str] = mapped_column(String(5000), nullable=False)
    sources: Mapped[dict] = mapped_column(JSON, nullable=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=True)
    model_id: Mapped[int] = mapped_column(ForeignKey("product_models.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
```

- [ ] **Step 6: 测试表创建**

重启 uvicorn，确认 `D:\RAG\backend\kb.db` 文件生成。
用 `python -c "from database import engine, Base; Base.metadata.create_all(bind=engine); print('OK')"` 验证。

---

### Task 3: 认证模块（JWT 登录/注册）

**Files:**
- Create: `backend/schemas/auth.py`
- Create: `backend/services/auth_service.py`
- Create: `backend/api/deps.py`
- Create: `backend/api/auth.py`
- Create: `backend/tests/test_auth.py`

- [ ] **Step 1: 创建 Auth Schemas**

```python
# backend/schemas/auth.py
from pydantic import BaseModel

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    password: str
    role: str = "customer"  # 注册时指定角色

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
```

- [ ] **Step 2: 创建 Auth Service**

```python
# backend/services/auth_service.py
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from db_models.user import User
from config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

def authenticate(db: Session, username: str, password: str) -> User:
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    return user

def register(db: Session, username: str, password: str, role: str = "customer") -> User:
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="用户名已存在")
    if role not in ("admin", "customer"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="无效的角色")
    user = User(username=username, password_hash=hash_password(password), role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
```

- [ ] **Step 3: 创建依赖注入**

```python
# backend/api/deps.py
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database import get_db
from config import settings
from db_models.user import User

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="无效的令牌")
    except JWTError:
        raise HTTPException(status_code=401, detail="无效的令牌")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")
    return current_user
```

- [ ] **Step 4: 创建 Auth Routes**

```python
# backend/api/auth.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from services.auth_service import authenticate, register, create_token
from api.deps import get_current_user, require_admin

router = APIRouter(prefix="/api/auth", tags=["认证"])

@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = authenticate(db, req.username, req.password)
    token = create_token({"sub": user.id, "role": user.role})
    return TokenResponse(access_token=token, role=user.role, username=user.username)

@router.post("/register")
def register_user(req: RegisterRequest, _=Depends(require_admin), db: Session = Depends(get_db)):
    user = register(db, req.username, req.password, req.role)
    return {"id": user.id, "username": user.username, "role": user.role}
```

- [ ] **Step 5: 挂载路由到 main.py**

```python
# 在 backend/main.py 的 lifespan 后面添加:
from api.auth import router as auth_router
app.include_router(auth_router)
```

- [ ] **Step 6: 创建测试**

```python
# backend/tests/test_auth.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

def test_register_requires_admin():
    r = client.post("/api/auth/register", json={"username": "test", "password": "123456", "role": "customer"})
    assert r.status_code == 401  # 无 token
```

- [ ] **Step 7: 运行测试**

```bash
cd D:\RAG\backend
conda activate rag
pytest tests/test_auth.py -v
```

预期：`test_health` PASS，`test_register_requires_admin` PASS

---

### Task 4: 产品管理 API

**Files:**
- Create: `backend/schemas/product.py`
- Create: `backend/services/product_service.py`
- Create: `backend/api/products.py`
- Create: `backend/tests/test_products.py`

- [ ] **Step 1: 创建 Schemas**

```python
# backend/schemas/product.py
from pydantic import BaseModel
from datetime import datetime

class ProductCreate(BaseModel):
    name: str
    description: str = ""

class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

class ProductOut(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime

    class Config:
        from_attributes = True
```

- [ ] **Step 2: 创建 Service**

```python
# backend/services/product_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException

from db_models.product import Product
from schemas.product import ProductCreate, ProductUpdate

def get_products(db: Session) -> list[Product]:
    return db.query(Product).order_by(Product.created_at.desc()).all()

def create_product(db: Session, data: ProductCreate, user_id: int) -> Product:
    product = Product(name=data.name, description=data.description, created_by=user_id)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product

def update_product(db: Session, product_id: int, data: ProductUpdate) -> Product:
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    if data.name is not None:
        product.name = data.name
    if data.description is not None:
        product.description = data.description
    db.commit()
    db.refresh(product)
    return product

def delete_product(db: Session, product_id: int):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    db.delete(product)
    db.commit()
```

- [ ] **Step 3: 创建 Routes**

```python
# backend/api/products.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from api.deps import get_current_user, require_admin
from schemas.product import ProductCreate, ProductUpdate, ProductOut
from services import product_service

router = APIRouter(prefix="/api/products", tags=["产品管理"])

@router.get("", response_model=list[ProductOut])
def list_products(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return product_service.get_products(db)

@router.post("", response_model=ProductOut)
def create_product(data: ProductCreate, db: Session = Depends(get_db), user=Depends(require_admin)):
    return product_service.create_product(db, data, user.id)

@router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, data: ProductUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    return product_service.update_product(db, product_id, data)

@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    product_service.delete_product(db, product_id)
    return {"detail": "已删除"}
```

- [ ] **Step 4: 挂载路由**

在 `main.py` 中添加：
```python
from api.products import router as product_router
app.include_router(product_router)
```

- [ ] **Step 5: 编写测试**

```python
# backend/tests/test_products.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def setup_admin_token():
    # 注册 admin + 登录获取 token
    r = client.post("/api/auth/register", json={"username": "admin_test", "password": "123456", "role": "admin"})
    # 首次运行没有 admin，需手动创建种子数据；测试先用 login
    ...

def test_get_products():
    r = client.get("/api/products")
    # 未登录也可浏览（设计中 get_current_user 依赖了认证，这里先验证 401）
    assert r.status_code == 401
```

- [ ] **Step 6: 运行测试**

```bash
pytest tests/test_products.py -v
```

---

### Task 5: 型号管理 API

**Files:**
- Create: `backend/schemas/product_model.py`
- Create: `backend/services/model_service.py`
- Create: `backend/api/product_models.py`

- [ ] **Step 1: 创建 Schemas**

```python
# backend/schemas/product_model.py
from pydantic import BaseModel
from datetime import datetime

class ModelCreate(BaseModel):
    product_id: int
    name: str
    description: str = ""

class ModelOut(BaseModel):
    id: int
    product_id: int
    name: str
    description: str
    created_at: datetime

    class Config:
        from_attributes = True
```

- [ ] **Step 2: 创建 Service**

```python
# backend/services/model_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException

from db_models.product_model import ProductModel
from schemas.product_model import ModelCreate

def get_models_by_product(db: Session, product_id: int) -> list[ProductModel]:
    return db.query(ProductModel).filter(ProductModel.product_id == product_id).order_by(ProductModel.created_at.desc()).all()

def create_model(db: Session, data: ModelCreate) -> ProductModel:
    model = ProductModel(product_id=data.product_id, name=data.name, description=data.description)
    db.add(model)
    db.commit()
    db.refresh(model)
    return model

def delete_model(db: Session, model_id: int):
    model = db.query(ProductModel).filter(ProductModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="型号不存在")
    db.delete(model)
    db.commit()
```

- [ ] **Step 3: 创建 Routes**

```python
# backend/api/product_models.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from api.deps import require_admin
from schemas.product_model import ModelCreate, ModelOut
from services import model_service

router = APIRouter(prefix="/api", tags=["型号管理"])

@router.get("/products/{product_id}/models", response_model=list[ModelOut])
def list_models(product_id: int, db: Session = Depends(get_db)):
    return model_service.get_models_by_product(db, product_id)

@router.post("/models", response_model=ModelOut)
def create_model(data: ModelCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    return model_service.create_model(db, data)

@router.delete("/models/{model_id}")
def delete_model(model_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    model_service.delete_model(db, model_id)
    return {"detail": "已删除"}
```

- [ ] **Step 4: 挂载路由并测试**

```bash
# 挂载到 main.py 后测试
pytest tests/test_products.py -v
```

---

### Task 6: 文档上传与处理 API

**Files:**
- Create: `backend/schemas/document.py`
- Create: `backend/services/document_service.py`
- Create: `backend/api/documents.py`
- Create: `backend/tests/test_documents.py`

- [ ] **Step 1: 创建 Schemas**

```python
# backend/schemas/document.py
from pydantic import BaseModel
from datetime import datetime

class DocumentOut(BaseModel):
    id: int
    model_id: int
    filename: str
    file_type: str
    file_size: int
    status: str
    chunk_count: int
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentStatus(BaseModel):
    id: int
    status: str
    chunk_count: int
```

- [ ] **Step 2: 创建 Document Service（基础 CRUD）**

```python
# backend/services/document_service.py
import os
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile

from db_models.document import Document
from config import settings

ALLOWED_TYPES = {"pdf": "pdf", "docx": "docx", "md": "md"}

def get_docs_by_model(db: Session, model_id: int) -> list[Document]:
    return db.query(Document).filter(Document.model_id == model_id).order_by(Document.created_at.desc()).all()

def save_upload_file(file: UploadFile) -> tuple[str, str, int]:
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: .{ext}")
    os.makedirs(settings.upload_dir, exist_ok=True)
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    file_path = os.path.join(settings.upload_dir, unique_name)
    content = file.file.read()
    if len(content) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"文件大小超过 {settings.max_upload_size_mb}MB 限制")
    with open(file_path, "wb") as f:
        f.write(content)
    return file_path, ALLOWED_TYPES[ext], len(content)

def create_document(db: Session, model_id: int, filename: str, file_type: str, file_path: str, file_size: int, user_id: int) -> Document:
    doc = Document(
        model_id=model_id, filename=filename, file_type=file_type,
        file_path=file_path, file_size=file_size, uploaded_by=user_id, status="processing"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc

def get_document_status(db: Session, doc_id: int) -> Document:
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    return doc

def delete_document(db: Session, doc_id: int):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="文档不存在")
    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)
    db.delete(doc)
    db.commit()
```

- [ ] **Step 3: 创建 Routes**

```python
# backend/api/documents.py
from fastapi import APIRouter, Depends, UploadFile, File, Form
from sqlalchemy.orm import Session

from database import get_db
from api.deps import get_current_user, require_admin
from schemas.document import DocumentOut, DocumentStatus
from services import document_service

router = APIRouter(prefix="/api", tags=["文档管理"])

@router.get("/models/{model_id}/docs", response_model=list[DocumentOut])
def list_docs(model_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return document_service.get_docs_by_model(db, model_id)

@router.post("/documents/upload")
async def upload(
    model_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(require_admin),
):
    file_path, file_type, file_size = document_service.save_upload_file(file)
    doc = document_service.create_document(db, model_id, file.filename, file_type, file_path, file_size, user.id)
    return DocumentOut.from_orm(doc)

@router.get("/documents/{doc_id}/status", response_model=DocumentStatus)
def get_status(doc_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    doc = document_service.get_document_status(db, doc_id)
    return DocumentStatus(id=doc.id, status=doc.status, chunk_count=doc.chunk_count)

@router.delete("/documents/{doc_id}")
def delete_doc(doc_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    document_service.delete_document(db, doc_id)
    return {"detail": "已删除"}
```

- [ ] **Step 4: 测试（无文件上传的基础测试）**

```python
# backend/tests/test_documents.py
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_list_docs_requires_auth():
    r = client.get("/api/models/1/docs")
    assert r.status_code == 401
```

```bash
pytest tests/test_documents.py -v
```

---

### Task 7: RAG Pipeline（Embedding + 文档摄入 + 检索）

**Files:**
- Create: `backend/rag/__init__.py`
- Create: `backend/rag/embeddings.py`
- Create: `backend/rag/ingestion.py`
- Create: `backend/rag/retrieval.py`
- Create: `backend/rag/prompt.py`

- [ ] **Step 1: 创建 Embedding 模块**

```python
# backend/rag/embeddings.py
from sentence_transformers import SentenceTransformer
from config import settings

_embedding_model = None

def get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(
            settings.embedding_model,
            device=settings.embedding_device
        )
    return _embedding_model
```

- [ ] **Step 2: 创建文档摄入模块**

```python
# backend/rag/ingestion.py
import os
from sqlalchemy.orm import Session
import chromadb
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core import Document as LlamaDocument

from config import settings
from rag.embeddings import get_embedding_model
from db_models.document import Document
from db_models.product_model import ProductModel
from db_models.product import Product

# ChromaDB 持久化客户端
_chroma_client = None

def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        os.makedirs(settings.chroma_persist_dir, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
    return _chroma_client

def get_or_create_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(name="knowledge_base")

def parse_file(file_path: str, file_type: str) -> str:
    if file_type == "pdf":
        import pdfplumber
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
        return text
    elif file_type == "docx":
        from docx import Document as DocxDoc
        doc = DocxDoc(file_path)
        return "\n".join(p.text for p in doc.paragraphs)
    elif file_type == "md":
        with open(file_path, encoding="utf-8") as f:
            return f.read()
    else:
        raise ValueError(f"不支持的文件类型: {file_type}")

def ingest_document(db: Session, doc_id: int):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        return
    try:
        # 获取关联的产品和型号名称（作为元数据）
        model = db.query(ProductModel).filter(ProductModel.id == doc.model_id).first()
        product = db.query(Product).filter(Product.id == model.product_id).first() if model else None

        # 解析文件内容
        text = parse_file(doc.file_path, doc.file_type)

        # 切片
        splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
        nodes = splitter.get_nodes_from_documents([LlamaDocument(text=text)])

        # 向量化 + 入库
        embed_model = get_embedding_model()
        collection = get_or_create_collection()

        for i, node in enumerate(nodes):
            embedding = embed_model.encode(node.text).tolist()
            collection.add(
                ids=[f"doc_{doc_id}_chunk_{i}"],
                embeddings=[embedding],
                documents=[node.text],
                metadatas=[{
                    "doc_id": doc_id,
                    "filename": doc.filename,
                    "product_name": product.name if product else "",
                    "model_name": model.name if model else "",
                    "chunk_index": i,
                }]
            )

        # 更新文档状态
        doc.status = "ready"
        doc.chunk_count = len(nodes)
        db.commit()
    except Exception as e:
        doc.status = "error"
        db.commit()
        raise e
```

- [ ] **Step 3: 创建检索模块**

```python
# backend/rag/retrieval.py
import chromadb
from rag.embeddings import get_embedding_model
from rag.ingestion import get_or_create_collection

def search(query: str, product_name: str = "", model_name: str = "", top_k: int = 5) -> list[dict]:
    embed_model = get_embedding_model()
    query_embedding = embed_model.encode(query).tolist()
    collection = get_or_create_collection()

    # 构建过滤条件
    where = {}
    if model_name:
        where["model_name"] = model_name
    elif product_name:
        where["product_name"] = product_name

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where if where else None,
    )

    chunks = []
    if results["ids"] and results["ids"][0]:
        for i in range(len(results["ids"][0])):
            chunks.append({
                "text": results["documents"][0][i],
                "filename": results["metadatas"][0][i].get("filename", ""),
                "product_name": results["metadatas"][0][i].get("product_name", ""),
                "model_name": results["metadatas"][0][i].get("model_name", ""),
                "score": results["distances"][0][i] if results.get("distances") else 0,
            })
    return chunks
```

- [ ] **Step 4: 创建 Prompt 模板**

```python
# backend/rag/prompt.py
def build_prompt(context_chunks: list[dict], question: str) -> str:
    context_text = "\n\n---\n".join(
        f"[来源: {c['product_name']}/{c['model_name']}/{c['filename']}]\n{c['text']}"
        for c in context_chunks
    )
    return f"""你是一个企业知识库助手。基于以下参考资料回答用户问题。
如果参考资料不足以回答问题，请如实告知，不要编造。

参考资料：
{context_text}

用户问题：{question}

要求：
1. 回答准确，引用具体文档来源
2. 如涉及多份资料，综合回答
3. 给出具体的操作步骤（如适用）"""
```

- [ ] **Step 5: 测试 Embedding 加载**

```bash
cd D:\RAG\backend
python -c "from rag.embeddings import get_embedding_model; m = get_embedding_model(); print('Embedding模型加载成功'); print('向量维度:', m.get_sentence_embedding_dimension())"
```

预期输出：Embedding模型加载成功，向量维度: 1024（首次运行会下载 BGE 模型，约 1.3GB）

---

### Task 8: 问答 API（含 SSE 流式）

**Files:**
- Create: `backend/schemas/chat.py`
- Create: `backend/services/chat_service.py`
- Create: `backend/api/chat.py`
- Create: `backend/tests/test_chat.py`

- [ ] **Step 1: 创建 Chat Schemas**

```python
# backend/schemas/chat.py
from pydantic import BaseModel

class ChatRequest(BaseModel):
    question: str
    product_id: int | None = None
    model_id: int | None = None
    product_name: str = ""
    model_name: str = ""

class ChatResponse(BaseModel):
    answer: str
    sources: list[dict]
```

- [ ] **Step 2: 创建 Chat Service**

```python
# backend/services/chat_service.py
from openai import OpenAI
from sqlalchemy.orm import Session

from config import settings
from rag.retrieval import search
from rag.prompt import build_prompt
from db_models.conversation import Conversation
from db_models.product import Product
from db_models.product_model import ProductModel

_client = None

def get_deepseek_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)
    return _client

def chat(db: Session, question: str, user_id: int, product_id: int = None, model_id: int = None) -> ChatResponse:
    # 解析产品/型号名称用于过滤
    product_name = ""
    model_name = ""
    if product_id:
        p = db.query(Product).filter(Product.id == product_id).first()
        if p:
            product_name = p.name
    if model_id:
        m = db.query(ProductModel).filter(ProductModel.id == model_id).first()
        if m:
            model_name = m.name
            if not product_name:
                p = db.query(Product).filter(Product.id == m.product_id).first()
                if p:
                    product_name = p.name

    # RAG 检索
    chunks = search(question, product_name=product_name, model_name=model_name)
    sources = [{"filename": c["filename"], "product_name": c["product_name"], "model_name": c["model_name"]} for c in chunks]

    # 构建 Prompt + 调用 LLM
    prompt = build_prompt(chunks, question)
    client = get_deepseek_client()
    resp = client.chat.completions.create(
        model=settings.deepseek_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=2000,
    )
    answer = resp.choices[0].message.content

    # 保存对话历史
    conv = Conversation(
        user_id=user_id, question=question, answer=answer,
        sources=sources, product_id=product_id, model_id=model_id
    )
    db.add(conv)
    db.commit()

    return {"answer": answer, "sources": sources}

def chat_stream(db: Session, question: str, user_id: int, product_id: int = None, model_id: int = None):
    # 同上检索逻辑...
    product_name, model_name = "", ""
    if product_id:
        p = db.query(Product).filter(Product.id == product_id).first()
        if p: product_name = p.name
    if model_id:
        m = db.query(ProductModel).filter(ProductModel.id == model_id).first()
        if m:
            model_name = m.name
            if not product_name:
                p = db.query(Product).filter(Product.id == m.product_id).first()
                if p: product_name = p.name

    chunks = search(question, product_name=product_name, model_name=model_name)
    prompt = build_prompt(chunks, question)
    client = get_deepseek_client()
    stream = client.chat.completions.create(
        model=settings.deepseek_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=2000,
        stream=True,
    )

    full_answer = ""
    for chunk in stream:
        if chunk.choices[0].delta.content:
            content = chunk.choices[0].delta.content
            full_answer += content
            yield f"data: {content}\n\n"

    # 保存对话
    sources = [{"filename": c["filename"], "product_name": c["product_name"], "model_name": c["model_name"]} for c in chunks]
    conv = Conversation(user_id=user_id, question=question, answer=full_answer, sources=sources, product_id=product_id, model_id=model_id)
    db.add(conv)
    db.commit()

    yield "data: [DONE]\n\n"

def get_conversations(db: Session, user_id: int, role: str) -> list[Conversation]:
    if role == "admin":
        return db.query(Conversation).order_by(Conversation.created_at.desc()).limit(50).all()
    return db.query(Conversation).filter(Conversation.user_id == user_id).order_by(Conversation.created_at.desc()).limit(50).all()
```

- [ ] **Step 3: 创建 Chat Routes**

```python
# backend/api/chat.py
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from api.deps import get_current_user
from schemas.chat import ChatRequest
from services.chat_service import chat, chat_stream, get_conversations

router = APIRouter(prefix="/api/chat", tags=["智能问答"])

@router.post("/ask")
def ask(req: ChatRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return chat(db, req.question, user.id, req.product_id, req.model_id)

@router.post("/stream")
def stream_ask(req: ChatRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return StreamingResponse(
        chat_stream(db, req.question, user.id, req.product_id, req.model_id),
        media_type="text/event-stream",
    )

@router.get("/conversations")
def list_conversations(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return get_conversations(db, user.id, user.role)
```

- [ ] **Step 4: 测试 Chat API（需要 DEEPSEEK_API_KEY）**

```bash
# 确认 .env 中有有效的 DEEPSEEK_API_KEY
pytest tests/test_chat.py -v
```

---

### Task 9: 用户管理 API

**Files:**
- Create: `backend/schemas/user.py`
- Create: `backend/services/user_service.py`
- Create: `backend/api/users.py`

- [ ] **Step 1: Schemas + Service + Routes**

```python
# backend/schemas/user.py
from pydantic import BaseModel
from datetime import datetime

class UserOut(BaseModel):
    id: int
    username: str
    role: str
    created_at: datetime
    class Config: from_attributes = True

class UserUpdateRole(BaseModel):
    role: str
```

```python
# backend/services/user_service.py
from sqlalchemy.orm import Session
from fastapi import HTTPException
from db_models.user import User

def get_users(db: Session) -> list[User]:
    return db.query(User).order_by(User.created_at.desc()).all()

def update_role(db: Session, user_id: int, new_role: str) -> User:
    if new_role not in ("admin", "customer"):
        raise HTTPException(status_code=400, detail="无效的角色")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.role = new_role
    db.commit()
    db.refresh(user)
    return user
```

```python
# backend/api/users.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from api.deps import require_admin
from schemas.user import UserOut, UserUpdateRole
from services import user_service

router = APIRouter(prefix="/api/users", tags=["用户管理"])

@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _=Depends(require_admin)):
    return user_service.get_users(db)

@router.put("/{user_id}", response_model=UserOut)
def update_role(user_id: int, data: UserUpdateRole, db: Session = Depends(get_db), _=Depends(require_admin)):
    return user_service.update_role(db, user_id, data.role)
```

- [ ] **Step 2: 挂载 + 测试**

```bash
# 挂载到 main.py
pytest tests/ -v  # 运行全部测试
```

---

### Task 10: 前端项目脚手架

**Files:**
- 用 Vite 创建项目
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/stores/authStore.ts`
- Create: `frontend/src/types/index.ts`

- [ ] **Step 1: 创建 Vite 项目**

```bash
cd D:\RAG
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install antd @ant-design/icons axios zustand react-router-dom
npm install -D @types/react-router-dom  # 如果 react-router-dom v6 内置类型则跳过
```

- [ ] **Step 2: 创建 API 客户端**

```typescript
// frontend/src/api/client.ts
import axios from "axios";
import { message } from "antd";

const client = axios.create({
  baseURL: "http://localhost:8000",
  timeout: 60000,
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (res) => res,
  (error) => {
    const msg = error.response?.data?.detail || "请求失败";
    message.error(msg);
    if (error.response?.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default client;
```

- [ ] **Step 3: 创建认证状态管理**

```typescript
// frontend/src/stores/authStore.ts
import { create } from "zustand";
import client from "../api/client";

interface AuthState {
  token: string | null;
  role: string;
  username: string;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem("token"),
  role: localStorage.getItem("role") || "",
  username: localStorage.getItem("username") || "",
  login: async (username, password) => {
    const res = await client.post("/api/auth/login", { username, password });
    const { access_token, role, username: un } = res.data;
    localStorage.setItem("token", access_token);
    localStorage.setItem("role", role);
    localStorage.setItem("username", un);
    set({ token: access_token, role, username: un });
  },
  logout: () => {
    localStorage.clear();
    set({ token: null, role: "", username: "" });
  },
}));
```

- [ ] **Step 4: 创建类型定义**

```typescript
// frontend/src/types/index.ts
export interface Product {
  id: number;
  name: string;
  description: string;
  created_at: string;
}

export interface ProductModel {
  id: number;
  product_id: number;
  name: string;
  description: string;
  created_at: string;
}

export interface Document {
  id: number;
  model_id: number;
  filename: string;
  file_type: string;
  file_size: number;
  status: "processing" | "ready" | "error";
  chunk_count: number;
  created_at: string;
}

export interface UserInfo {
  id: number;
  username: string;
  role: "admin" | "customer";
  created_at: string;
}
```

- [ ] **Step 5: 验证启动**

```bash
cd D:\RAG\frontend
npm run dev
```

打开 `http://localhost:5173`，确认 Vite 默认页面可见。

---

### Task 11: 前端 — 登录页 + 布局

**Files:**
- Create: `frontend/src/pages/Login.tsx`
- Create: `frontend/src/components/AppLayout.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: 登录页**

```tsx
// frontend/src/pages/Login.tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Form, Input, Button, Card, Typography, message } from "antd";
import { UserOutlined, LockOutlined } from "@ant-design/icons";
import { useAuthStore } from "../stores/authStore";

export default function Login() {
  const [loading, setLoading] = useState(false);
  const login = useAuthStore((s) => s.login);
  const navigate = useNavigate();

  const onFinish = async (values: { username: string; password: string }) => {
    setLoading(true);
    try {
      await login(values.username, values.password);
      message.success("登录成功");
      navigate("/");
    } catch {
      // 错误已在拦截器处理
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ height: "100vh", display: "flex", justifyContent: "center", alignItems: "center", background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)" }}>
      <Card style={{ width: 400, boxShadow: "0 4px 24px rgba(0,0,0,0.15)" }}>
        <h2 style={{ textAlign: "center", marginBottom: 32 }}>企业知识库</h2>
        <Form onFinish={onFinish} size="large">
          <Form.Item name="username" rules={[{ required: true, message: "请输入用户名" }]}>
            <Input prefix={<UserOutlined />} placeholder="用户名" />
          </Form.Item>
          <Form.Item name="password" rules={[{ required: true, message: "请输入密码" }]}>
            <Input.Password prefix={<LockOutlined />} placeholder="密码" />
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" block loading={loading}>登录</Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  );
}
```

- [ ] **Step 2: 全局布局**

```tsx
// frontend/src/components/AppLayout.tsx
import { Outlet, useNavigate, useLocation } from "react-router-dom";
import { Layout, Menu, Button, Typography } from "antd";
import {
  DashboardOutlined, FolderOutlined, MessageOutlined,
  UserOutlined, LogoutOutlined, SettingOutlined
} from "@ant-design/icons";
import { useAuthStore } from "../stores/authStore";

const { Header, Sider, Content } = Layout;

export default function AppLayout() {
  const { role, username, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    { key: "/", icon: <DashboardOutlined />, label: "首页" },
    ...(role === "admin" ? [{ key: "/knowledge", icon: <FolderOutlined />, label: "知识库" }] : []),
    { key: "/chat", icon: <MessageOutlined />, label: "问答" },
    ...(role === "admin" ? [{ key: "/users", icon: <UserOutlined />, label: "用户管理" }] : []),
  ];

  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Sider breakpoint="lg" collapsedWidth="0">
        <div style={{ height: 64, display: "flex", alignItems: "center", justifyContent: "center" }}>
          <Typography.Text strong style={{ color: "#fff", fontSize: 18 }}>企业知识库</Typography.Text>
        </div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={({ key }) => navigate(key)}
        />
      </Sider>
      <Layout>
        <Header style={{ background: "#fff", padding: "0 24px", display: "flex", justifyContent: "flex-end", alignItems: "center", gap: 16 }}>
          <span>{username}（{role === "admin" ? "管理员" : "客户"}）</span>
          <Button icon={<LogoutOutlined />} onClick={() => { logout(); navigate("/login"); }}>退出</Button>
        </Header>
        <Content style={{ margin: 24, background: "#fff", padding: 24, borderRadius: 8 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  );
}
```

- [ ] **Step 3: 更新 App.tsx 路由**

```tsx
// frontend/src/App.tsx
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ConfigProvider } from "antd";
import zhCN from "antd/locale/zh_CN";
import Login from "./pages/Login";
import AppLayout from "./components/AppLayout";

function Protected() {
  const token = localStorage.getItem("token");
  if (!token) return <Navigate to="/login" replace />;
  return <AppLayout />;
}

export default function App() {
  return (
    <ConfigProvider locale={zhCN}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/*" element={<Protected />}>
            <Route index element={<div>首页（待实现）</div>} />
            <Route path="knowledge" element={<div>知识库（待实现）</div>} />
            <Route path="chat" element={<div>问答（待实现）</div>} />
            <Route path="users" element={<div>用户管理（待实现）</div>} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
}
```

- [ ] **Step 4: 测试**

```bash
cd D:\RAG\frontend
npm run dev
```

验证：访问 `http://localhost:5173`，自动跳转登录页。登录成功后进入布局页面，侧边栏/Header 正常显示，customer 用户看不到"知识库"和"用户管理"菜单。

---

### Task 12: 前端 — 首页 Dashboard

**Files:**
- Create: `frontend/src/pages/Dashboard.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: 创建 Dashboard**

```tsx
// frontend/src/pages/Dashboard.tsx
import { useEffect, useState } from "react";
import { Row, Col, Card, Statistic, Typography } from "antd";
import { FolderOutlined, FileOutlined, MessageOutlined } from "@ant-design/icons";
import { useNavigate } from "react-router-dom";
import client from "../api/client";

export default function Dashboard() {
  const [stats, setStats] = useState({ products: 0, documents: 0, conversations: 0 });
  const navigate = useNavigate();

  useEffect(() => {
    Promise.all([
      client.get("/api/products"),
      client.get("/api/chat/conversations"),
    ]).then(([productsRes, convsRes]) => {
      setStats({
        products: productsRes.data.length,
        documents: 0,  // 需要从产品/型号遍历获取，简化处理
        conversations: convsRes.data.length,
      });
    }).catch(() => {});
  }, []);

  return (
    <div>
      <Typography.Title level={4}>知识库概览</Typography.Title>
      <Row gutter={24} style={{ marginTop: 24 }}>
        <Col xs={24} sm={8}>
          <Card hoverable onClick={() => navigate("/knowledge")}>
            <Statistic title="产品线" value={stats.products} prefix={<FolderOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card hoverable onClick={() => navigate("/knowledge")}>
            <Statistic title="文档总数" value={stats.documents} prefix={<FileOutlined />} />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card hoverable onClick={() => navigate("/chat")}>
            <Statistic title="今日问答" value={stats.conversations} prefix={<MessageOutlined />} />
          </Card>
        </Col>
      </Row>
    </div>
  );
}
```

- [ ] **Step 2: 更新路由**

在 `App.tsx` 中将 `index` 路由替换为：
```tsx
import Dashboard from "./pages/Dashboard";
// ...
<Route index element={<Dashboard />} />
```

- [ ] **Step 3: 测试**

打开首页，确认统计卡片渲染正常，点击卡片可跳转。

---

### Task 13: 前端 — 知识库管理页

**Files:**
- Create: `frontend/src/pages/KnowledgeBase.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: 创建知识库管理页（三栏布局）**

```tsx
// frontend/src/pages/KnowledgeBase.tsx
import { useEffect, useState } from "react";
import { Row, Col, Card, List, Button, Modal, Form, Input, Upload, Tag, Popconfirm, message, Typography } from "antd";
import { PlusOutlined, DeleteOutlined, UploadOutlined } from "@ant-design/icons";
import client from "../api/client";
import type { Product, ProductModel, Document } from "../types";

export default function KnowledgeBase() {
  const [products, setProducts] = useState<Product[]>([]);
  const [models, setModels] = useState<ProductModel[]>([]);
  const [docs, setDocs] = useState<Document[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [selectedModel, setSelectedModel] = useState<ProductModel | null>(null);
  const [productModalOpen, setProductModalOpen] = useState(false);
  const [modelModalOpen, setModelModalOpen] = useState(false);

  const loadProducts = () => client.get("/api/products").then(r => setProducts(r.data));
  const loadModels = (productId: number) => client.get(`/api/products/${productId}/models`).then(r => setModels(r.data));
  const loadDocs = (modelId: number) => client.get(`/api/models/${modelId}/docs`).then(r => setDocs(r.data));

  useEffect(() => { loadProducts(); }, []);

  const handleProductClick = (p: Product) => {
    setSelectedProduct(p);
    setSelectedModel(null);
    setDocs([]);
    loadModels(p.id);
  };

  const handleModelClick = (m: ProductModel) => {
    setSelectedModel(m);
    loadDocs(m.id);
  };

  const handleUpload = async (modelId: number, file: File) => {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("model_id", String(modelId));
    try {
      await client.post("/api/documents/upload", formData);
      message.success("上传成功");
      loadDocs(modelId);
    } catch { /* 拦截器处理 */ }
  };

  const statusColor: Record<string, string> = { processing: "blue", ready: "green", error: "red" };
  const statusText: Record<string, string> = { processing: "处理中", ready: "就绪", error: "失败" };

  return (
    <div>
      <Typography.Title level={4}>知识库管理</Typography.Title>
      <Row gutter={16}>
        {/* 产品列表 */}
        <Col span={8}>
          <Card title="产品线" extra={<Button icon={<PlusOutlined />} size="small" onClick={() => setProductModalOpen(true)}>新增</Button>}>
            <List dataSource={products} renderItem={p => (
              <List.Item onClick={() => handleProductClick(p)}
                style={{ cursor: "pointer", background: selectedProduct?.id === p.id ? "#e6f7ff" : undefined, padding: 8, borderRadius: 4 }}>
                <span>{p.name}</span>
                <Popconfirm title="确定删除？" onConfirm={() => client.delete(`/api/products/${p.id}`).then(loadProducts)}>
                  <Button size="small" danger icon={<DeleteOutlined />} />
                </Popconfirm>
              </List.Item>
            )} />
          </Card>
        </Col>
        {/* 型号列表 */}
        <Col span={8}>
          <Card title="型号" extra={selectedProduct && <Button icon={<PlusOutlined />} size="small" onClick={() => setModelModalOpen(true)}>新增</Button>}>
            {selectedProduct ? (
              <List dataSource={models} renderItem={m => (
                <List.Item onClick={() => handleModelClick(m)}
                  style={{ cursor: "pointer", background: selectedModel?.id === m.id ? "#e6f7ff" : undefined, padding: 8, borderRadius: 4 }}>
                  <span>{m.name}</span>
                  <Popconfirm title="确定删除？" onConfirm={() => client.delete(`/api/models/${m.id}`).then(() => loadModels(selectedProduct.id))}>
                    <Button size="small" danger icon={<DeleteOutlined />} />
                  </Popconfirm>
                </List.Item>
              )} />
            ) : <Typography.Text type="secondary">请先选择产品</Typography.Text>}
          </Card>
        </Col>
        {/* 文档列表 */}
        <Col span={8}>
          <Card title="文档" extra={selectedModel && (
            <Upload beforeUpload={(file) => { handleUpload(selectedModel.id, file); return false; }} showUploadList={false}>
              <Button icon={<UploadOutlined />} size="small">上传</Button>
            </Upload>
          )}>
            {selectedModel ? (
              <List dataSource={docs} renderItem={d => (
                <List.Item style={{ padding: 8 }}>
                  <span>{d.filename}</span>
                  <Tag color={statusColor[d.status]}>{statusText[d.status]}</Tag>
                  <Popconfirm title="确定删除？" onConfirm={() => client.delete(`/api/documents/${d.id}`).then(() => loadDocs(selectedModel.id))}>
                    <Button size="small" danger icon={<DeleteOutlined />} />
                  </Popconfirm>
                </List.Item>
              )} />
            ) : <Typography.Text type="secondary">请先选择型号</Typography.Text>}
          </Card>
        </Col>
      </Row>

      {/* 新增产品弹窗 */}
      <Modal title="新增产品" open={productModalOpen} onCancel={() => setProductModalOpen(false)} footer={null}>
        <Form onFinish={async (v) => { await client.post("/api/products", v); setProductModalOpen(false); loadProducts(); }}>
          <Form.Item name="name" rules={[{ required: true }]}><Input placeholder="产品名称" /></Form.Item>
          <Form.Item name="description"><Input.TextArea placeholder="描述" /></Form.Item>
          <Button type="primary" htmlType="submit">确定</Button>
        </Form>
      </Modal>

      {/* 新增型号弹窗 */}
      <Modal title="新增型号" open={modelModalOpen} onCancel={() => setModelModalOpen(false)} footer={null}>
        <Form onFinish={async (v) => { await client.post("/api/models", { ...v, product_id: selectedProduct?.id }); setModelModalOpen(false); loadModels(selectedProduct!.id); }}>
          <Form.Item name="name" rules={[{ required: true }]}><Input placeholder="型号名称" /></Form.Item>
          <Form.Item name="description"><Input.TextArea placeholder="描述" /></Form.Item>
          <Button type="primary" htmlType="submit">确定</Button>
        </Form>
      </Modal>
    </div>
  );
}
```

- [ ] **Step 2: 更新路由**

```tsx
import KnowledgeBase from "./pages/KnowledgeBase";
// 替换 knowledge 路由
<Route path="knowledge" element={<KnowledgeBase />} />
```

- [ ] **Step 3: 测试**

访问知识库页面，确认三栏布局、级联选择、新增/删除产品、型号、文档上传功能正常。
上传一个测试 PDF 文件，检查 status badge 是否从 "处理中" 变为 "就绪"。

---

### Task 14: 前端 — 问答页（含 SSE 流式）

**Files:**
- Create: `frontend/src/pages/Chat.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: 创建 Chat 页面**

```tsx
// frontend/src/pages/Chat.tsx
import { useState, useRef, useEffect } from "react";
import { Input, Button, Select, Space, Typography, Card, Tag, Spin } from "antd";
import { SendOutlined, RobotOutlined, UserOutlined } from "@ant-design/icons";
import { useAuthStore } from "../stores/authStore";
import client from "../api/client";
import type { Product, ProductModel } from "../types";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: { filename: string; product_name: string; model_name: string }[];
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [products, setProducts] = useState<Product[]>([]);
  const [models, setModels] = useState<ProductModel[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<number | undefined>();
  const [selectedModel, setSelectedModel] = useState<number | undefined>();
  const chatRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    client.get("/api/products").then(r => setProducts(r.data));
  }, []);

  useEffect(() => {
    if (selectedProduct) {
      client.get(`/api/products/${selectedProduct}/models`).then(r => setModels(r.data));
    } else {
      setModels([]);
      setSelectedModel(undefined);
    }
  }, [selectedProduct]);

  const scrollBottom = () => {
    setTimeout(() => { chatRef.current?.scrollTo({ top: chatRef.current.scrollHeight, behavior: "smooth" }); }, 100);
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const question = input.trim();
    setInput("");
    setMessages(prev => [...prev, { role: "user", content: question }]);
    setLoading(true);
    scrollBottom();

    try {
      const token = localStorage.getItem("token");
      const res = await fetch("http://localhost:8000/api/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ question, product_id: selectedProduct, model_id: selectedModel }),
      });

      const reader = res.body?.getReader();
      const decoder = new TextDecoder();
      let answer = "";

      setMessages(prev => [...prev, { role: "assistant", content: "" }]);

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;
        const text = decoder.decode(value);
        const lines = text.split("\n");
        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            if (data === "[DONE]") break;
            answer += data;
            setMessages(prev => {
              const copy = [...prev];
              copy[copy.length - 1] = { ...copy[copy.length - 1], role: "assistant", content: answer };
              return copy;
            });
            scrollBottom();
          }
        }
      }
    } catch {
      setMessages(prev => {
        const copy = [...prev];
        copy[copy.length - 1] = { ...copy[copy.length - 1], content: "AI 服务不可用，请稍后重试" };
        return copy;
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 160px)" }}>
      <Space style={{ marginBottom: 16 }}>
        <Select placeholder="全部产品" allowClear style={{ width: 180 }}
          options={products.map(p => ({ value: p.id, label: p.name }))}
          value={selectedProduct} onChange={v => setSelectedProduct(v)} />
        <Select placeholder="全部型号" allowClear style={{ width: 180 }}
          options={models.map(m => ({ value: m.id, label: m.name }))}
          value={selectedModel} onChange={v => setSelectedModel(v)} />
      </Space>

      <div ref={chatRef} style={{ flex: 1, overflow: "auto", marginBottom: 16, background: "#f5f5f5", borderRadius: 8, padding: 16 }}>
        {messages.length === 0 && (
          <div style={{ textAlign: "center", color: "#999", marginTop: 80 }}>
            <RobotOutlined style={{ fontSize: 48 }} />
            <p>我是企业知识库助手，请提出你的问题</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} style={{ marginBottom: 16, display: "flex", justifyContent: msg.role === "user" ? "flex-end" : "flex-start" }}>
            <Card size="small" style={{ maxWidth: "80%", background: msg.role === "user" ? "#e6f7ff" : "#fff" }}>
              <Space align="start">
                {msg.role === "assistant" ? <RobotOutlined style={{ color: "#1677ff" }} /> : <UserOutlined />}
                <div>
                  <Typography.Paragraph style={{ margin: 0, whiteSpace: "pre-wrap" }}>
                    {msg.content}
                    {loading && i === messages.length - 1 && msg.role === "assistant" && <Spin size="small" style={{ marginLeft: 8 }} />}
                  </Typography.Paragraph>
                  {msg.sources && msg.sources.length > 0 && (
                    <div style={{ marginTop: 8 }}>
                      <Typography.Text type="secondary" style={{ fontSize: 12 }}>来源：</Typography.Text>
                      {msg.sources.map((s, j) => (
                        <Tag key={j} color="blue" style={{ fontSize: 11 }}>
                          {s.product_name}/{s.model_name}/{s.filename}
                        </Tag>
                      ))}
                    </div>
                  )}
                </div>
              </Space>
            </Card>
          </div>
        ))}
      </div>

      <div style={{ display: "flex", gap: 8 }}>
        <Input.TextArea value={input} onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendMessage(); } }}
          placeholder="输入问题，按 Enter 发送..." rows={2} />
        <Button type="primary" icon={<SendOutlined />} onClick={sendMessage} loading={loading}>发送</Button>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 更新路由**

```tsx
import ChatPage from "./pages/Chat";
<Route path="chat" element={<ChatPage />} />
```

- [ ] **Step 3: 测试**

打开问答页，输入问题并发送。确认：
- 流式逐字渲染正常
- 引用来源标签显示
- 产品/型号下拉可限定范围

---

### Task 15: 前端 — 用户管理页

**Files:**
- Create: `frontend/src/pages/UserManagement.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: 创建用户管理页**

```tsx
// frontend/src/pages/UserManagement.tsx
import { useEffect, useState } from "react";
import { Table, Button, Select, message, Typography } from "antd";
import client from "../api/client";
import type { UserInfo } from "../types";

export default function UserManagement() {
  const [users, setUsers] = useState<UserInfo[]>([]);

  const loadUsers = () => client.get("/api/users").then(r => setUsers(r.data));

  useEffect(() => { loadUsers(); }, []);

  const changeRole = async (userId: number, newRole: string) => {
    await client.put(`/api/users/${userId}`, { role: newRole });
    message.success("角色已更新");
    loadUsers();
  };

  const columns = [
    { title: "ID", dataIndex: "id", key: "id" },
    { title: "用户名", dataIndex: "username", key: "username" },
    {
      title: "角色", dataIndex: "role", key: "role",
      render: (role: string, record: UserInfo) => (
        <Select value={role} style={{ width: 120 }} onChange={v => changeRole(record.id, v)}>
          <Select.Option value="admin">管理员</Select.Option>
          <Select.Option value="customer">客户</Select.Option>
        </Select>
      )
    },
    { title: "创建时间", dataIndex: "created_at", key: "created_at", render: (v: string) => new Date(v).toLocaleDateString() },
  ];

  return (
    <div>
      <Typography.Title level={4}>用户管理</Typography.Title>
      <Table rowKey="id" dataSource={users} columns={columns} />
    </div>
  );
}
```

- [ ] **Step 2: 更新路由**

```tsx
import UserManagement from "./pages/UserManagement";
<Route path="users" element={<UserManagement />} />
```

- [ ] **Step 3: 测试**

以 admin 登录，确认用户列表可加载，角色切换功能正常。
以 customer 登录，确认无法访问 `/users`。

---

### Task 16: 集成测试 + 正确性验证

- [ ] **Step 1: 运行后端全部测试**

```bash
cd D:\RAG\backend
conda activate rag
pytest tests/ -v
```

- [ ] **Step 2: 前端构建验证**

```bash
cd D:\RAG\frontend
npm run build
```

确认无 TypeScript 编译错误。

- [ ] **Step 3: 端到端场景测试**

1. 启动后端：`uvicorn main:app --reload --port 8000`
2. 启动前端：`npm run dev`
3. 用 admin 账号登录
4. 创建产品 "智能手表" → 型号 "X1" → 上传测试 PDF
5. 等待文档状态变为 "就绪"
6. 在问答页提问，验证流式回答 + 来源引用
7. 创建 customer 账号，验证只有首页+问答菜单

- [ ] **Step 4: 边界情况测试**

- 上传不支持的文件类型（如 .exe）→ 400 错误
- 上传超 50MB 文件 → 413 错误
- 不传 token 访问受保护接口 → 401
- customer 调用 admin API → 403
- 删除有型号的产品 → 级联删除正常

- [ ] **Step 5: 写进度记录**

更新 `D:\RAG\docs\progress.md`，记录开发完成情况和测试结果。

---

## 开发顺序依赖

```
Task 1 (脚手架) → Task 2 (数据模型) → Task 3 (认证)
                                         ↓
                              Task 4 (产品) → Task 5 (型号) → Task 6 (文档)
                                                                  ↓
                                                            Task 7 (RAG) → Task 8 (问答)
                                                                                ↓
                                                                          Task 9 (用户管理)
                                                                                ↓
Task 10 (前端脚手架) → Task 11 (登录+布局) → Task 12 (Dashboard)
                         ↓                      ↓
                    Task 13 (知识库)     Task 14 (问答) → Task 15 (用户管理)
                                                              ↓
                                                        Task 16 (集成测试)
```
