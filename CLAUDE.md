# RAG Enterprise Knowledge Base

企业级 RAG 知识库系统，基于 FastAPI + React + ChromaDB + DeepSeek LLM。

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy (SQLite), ChromaDB, LlamaIndex, sentence-transformers
- **Frontend**: React 18 + TypeScript + Ant Design 5 + Vite
- **LLM**: DeepSeek (deepseek-chat), OpenAI-compatible API
- **Embedding**: BAAI/bge-large-zh-v1.5 (Chinese-optimized)
- **OCR**: RapidOCR (ONNX Runtime)

## Directory Structure

```
RAG/
├── backend/
│   ├── main.py              # FastAPI app entry, CORS, static serve
│   ├── config.py            # Settings (DB path, API keys, models)
│   ├── database.py          # SQLAlchemy engine + Base
│   ├── api/                 # Route handlers (auth, chat, documents, products, users)
│   ├── services/            # Business logic (auth, chat, document, user)
│   ├── db_models/           # SQLAlchemy models (User, Product, Document, Conversation)
│   ├── schemas/             # Pydantic request/response models
│   ├── rag/                 # RAG pipeline
│   │   ├── embeddings.py    # Embedding model singleton
│   │   ├── ingestion.py     # Document parse → chunk → embed → ChromaDB
│   │   ├── retrieval.py     # Query → embed → search ChromaDB
│   │   ├── translator.py    # Language detection + DeepSeek translation (EN→ZH)
│   │   ├── ocr.py           # RapidOCR for images in PDFs
│   │   └── prompt.py        # System prompt builder
│   └── tests/               # pytest tests
├── frontend/
│   └── src/pages/           # Chat, Dashboard, KnowledgeBase, Login, UserManagement
└── docs/                    # Design doc, progress log, plans
```

## How to Start

```bash
# Backend (requires Python env with dependencies)
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend dev mode
cd frontend
npm run dev

# Frontend production build (backend serves from dist/)
cd frontend && npm run build
```

## Key Notes

- **Python env**: `anaconda3/envs/rag` (contains sentence-transformers, chromadb, etc.)
- **DB**: SQLite at `backend/kb.db`, ChromaDB at `backend/chroma_data/`
- **.env** at `backend/.env` has `DEEPSEEK_API_KEY` and `SECRET_KEY` — NEVER commit this file
- **File uploads** go to `backend/uploads/`
- **Port**: Backend 8000, Frontend dev 5173 — but production only needs 8000 (backend serves frontend)
- **API base URL** is empty (relative) — ready for LAN/cloud deployment
- **CORS** currently `*` (allow all) — for team LAN access
- **Supported file types**: PDF, DOCX, MD, TXT
- **English docs** are auto-detected and translated to Chinese via DeepSeek before embedding
- **OCR** enabled for images embedded in PDFs (config `enable_ocr`)

## User Roles

- **admin**: Upload/delete documents, manage products/models/users, chat
- **customer**: Chat only

Default admin: `admin / admin`

## Git

- `master`: current development
- `deployment`: snapshot before network-access changes
- Remote: `https://github.com/zebeirongzhi/RAG-Enterprise-Knowledge-Base`
