import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

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


# Serve frontend static files in production (SPA fallback)
frontend_dist = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
_frontend_dist = frontend_dist

if os.path.exists(frontend_dist):

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Serve static files that exist on disk
        file_path = os.path.join(_frontend_dist, full_path) if full_path else ""
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        # Fallback to index.html for SPA routing
        index = os.path.join(_frontend_dist, "index.html")
        return FileResponse(index)
