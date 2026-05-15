# D:\RAG\backend\main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from api.auth import router as auth_router
from api.products import router as product_router
from api.product_models import router as model_router
from api.documents import router as doc_router
from api.chat import router as chat_router
from api.users import router as user_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时创建表
    Base.metadata.create_all(bind=engine)
    # 预加载 Embedding 模型，确保后台向量化任务可用
    from rag.embeddings import get_embedding_model
    get_embedding_model()
    yield


app = FastAPI(title="企业知识库 API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(product_router)
app.include_router(model_router)
app.include_router(doc_router)
app.include_router(chat_router)
app.include_router(user_router)

@app.get("/api/health")
def health():
    return {"status": "ok"}
