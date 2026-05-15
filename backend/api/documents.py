from fastapi import APIRouter, Depends, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session

from database import get_db, SessionLocal
from api.deps import get_current_user, require_admin
from schemas.document import DocumentOut, DocumentStatus
from services import document_service
from db_models.document import Document
from rag.ingestion import ingest_document

import logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["文档管理"])

def _run_ingestion(doc_id: int):
    """后台运行文档向量化"""
    db = SessionLocal()
    try:
        ingest_document(db, doc_id)
    except Exception:
        logger.exception(f"Background ingestion failed for document {doc_id}")
        try:
            doc = db.query(Document).filter(Document.id == doc_id).first()
            if doc and doc.status == "processing":
                doc.status = "error"
                db.commit()
        except Exception:
            logger.exception(f"Failed to update document {doc_id} status to error")
    finally:
        db.close()

@router.get("/documents/count")
def count_docs(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return {"count": document_service.count_documents(db)}

@router.get("/models/{model_id}/docs", response_model=list[DocumentOut])
def list_docs(model_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return document_service.get_docs_by_model(db, model_id)

@router.post("/documents/upload")
async def upload(
    model_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(require_admin),
    bg: BackgroundTasks = None,
):
    file_path, file_type, file_size = document_service.save_upload_file(file)
    doc = document_service.create_document(db, model_id, file.filename, file_type, file_path, file_size, user.id)
    bg.add_task(_run_ingestion, doc.id)
    return DocumentOut.model_validate(doc)

@router.get("/documents/{doc_id}/status", response_model=DocumentStatus)
def get_status(doc_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    doc = document_service.get_document_status(db, doc_id)
    return DocumentStatus(id=doc.id, status=doc.status, chunk_count=doc.chunk_count)

@router.delete("/documents/{doc_id}")
def delete_doc(doc_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    document_service.delete_document(db, doc_id)
    return {"detail": "已删除"}
