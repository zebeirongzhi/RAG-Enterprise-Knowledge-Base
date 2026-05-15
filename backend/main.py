import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from database import engine, Base
from api.auth import router as auth_router
from api.products import router as product_router
from api.product_models import router as model_router
from api.documents import router as doc_router
from api.chat import router as chat_router
from api.users import router as user_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    from rag.embeddings import get_embedding_model
    get_embedding_model()
    yield


app = FastAPI(title="企业知识库 API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(auth_router)
app.include_router(product_router)
app.include_router(model_router)
app.include_router(doc_router)
app.include_router(chat_router)
app.include_router(user_router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


# Serve frontend static files in production
frontend_dist = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
if os.path.exists(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
