import os
import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException, UploadFile

from db_models.document import Document
from config import settings

ALLOWED_TYPES = {"pdf": "pdf", "docx": "docx", "md": "md", "txt": "txt"}

def count_documents(db: Session) -> int:
    return db.query(Document).count()

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

    from rag.ingestion import get_or_create_collection
    try:
        collection = get_or_create_collection()
        # Get all chunk IDs for this document and delete them
        existing = collection.get(where={"doc_id": str(doc_id)})
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
    except Exception:
        pass

    db.delete(doc)
    db.commit()
