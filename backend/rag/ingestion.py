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
from db_models.user import User  # ensure FK resolution during flush

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
        from rag.ocr import ocr_page_image

        text = ""
        with pdfplumber.open(file_path) as pdf:
            total = len(pdf.pages)
            for i, page in enumerate(pdf.pages):
                t = page.extract_text()
                if t:
                    text += t + "\n"

                if settings.enable_ocr:
                    try:
                        img = page.to_image(resolution=200)
                        ocr_text = ocr_page_image(img.original)
                        if ocr_text:
                            text += ocr_text + "\n"
                        logger.info(f"OCR page {i+1}/{total}: {len(ocr_text)} chars from image")
                    except Exception:
                        logger.warning(f"OCR failed for page {i+1}/{total}", exc_info=True)

        return text
    elif file_type == "docx":
        from docx import Document as DocxDoc
        doc = DocxDoc(file_path)
        return "\n".join(p.text for p in doc.paragraphs)
    elif file_type == "md":
        with open(file_path, encoding="utf-8") as f:
            return f.read()
    elif file_type == "txt":
        with open(file_path, encoding="utf-8") as f:
            return f.read()
    else:
        raise ValueError(f"不支持的文件类型: {file_type}")


import logging
logger = logging.getLogger(__name__)


def ingest_document(db: Session, doc_id: int):
    """Parse a document, chunk it, embed chunks, store in ChromaDB."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        logger.warning(f"Document {doc_id} not found, skipping ingestion")
        return
    try:
        logger.info(f"Ingesting document {doc_id}: {doc.filename}")

        model = db.query(ProductModel).filter(ProductModel.id == doc.model_id).first()
        product = db.query(Product).filter(Product.id == model.product_id).first() if model else None

        text = parse_file(doc.file_path, doc.file_type)
        logger.info(f"Parsed {doc.file_type} file, {len(text)} characters")

        from rag.translator import detect_language, translate_to_chinese
        lang = detect_language(text)
        if lang == "en":
            logger.info(f"Document {doc_id} is English, translating to Chinese...")
            text = translate_to_chinese(text)
            logger.info(f"Translation complete, {len(text)} Chinese characters")

        splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
        nodes = splitter.get_nodes_from_documents([LlamaDocument(text=text)])
        logger.info(f"Split into {len(nodes)} chunks")

        embed_model = get_embedding_model()
        collection = get_or_create_collection()

        # Remove any existing chunks for this document (handles re-ingestion)
        existing = collection.get(where={"doc_id": str(doc_id)})
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
            logger.info(f"Removed {len(existing['ids'])} old chunks for document {doc_id}")

        for i, node in enumerate(nodes):
            embedding = embed_model.encode(node.text).tolist()
            collection.add(
                ids=[f"doc_{doc_id}_chunk_{i}"],
                embeddings=[embedding],
                documents=[node.text],
                metadatas=[{
                    "doc_id": str(doc_id),
                    "filename": doc.filename,
                    "product_name": product.name if product else "",
                    "model_name": model.name if model else "",
                    "chunk_index": i,
                }]
            )

        doc.status = "ready"
        doc.chunk_count = len(nodes)
        db.commit()
        logger.info(f"Document {doc_id} ingestion complete, {len(nodes)} chunks stored")
    except Exception as e:
        logger.error(f"Document {doc_id} ingestion failed: {e}", exc_info=True)
        db.rollback()
        doc.status = "error"
        db.commit()
