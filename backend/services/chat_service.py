import json
import re
from openai import OpenAI
from fastapi import HTTPException
from sqlalchemy.orm import Session

from config import settings
from rag.retrieval import search
from rag.prompt import build_prompt
from db_models.conversation import Conversation
from db_models.product import Product
from db_models.product_model import ProductModel

_client = None


def _normalize_markdown(text: str) -> str:
    """Fix common markdown formatting issues from LLM output."""
    # Add blank line before ## / ### headings
    text = re.sub(r"(?<!\n\n)(#{2,3}\s)", r"\n\n\1", text)
    # Remove blank lines between consecutive numbered list items (keeps them in one list)
    text = re.sub(r"(\d+\.\s.+)\n\n(\d+\.\s)", r"\1\n\2", text)
    # Remove blank lines between consecutive bullet items
    text = re.sub(r"(-\s.+)\n\n(-\s)", r"\1\n\2", text)
    # Collapse 3+ blank lines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def get_deepseek_client():
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.deepseek_api_key, base_url=settings.deepseek_base_url)
    return _client

def resolve_names(db: Session, product_id: int = None, model_id: int = None) -> tuple[str, str]:
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
    return product_name, model_name

def chat(db: Session, question: str, user_id: int, product_id: int = None, model_id: int = None) -> dict:
    product_name, model_name = resolve_names(db, product_id, model_id)
    chunks = search(question, product_name=product_name, model_name=model_name)
    sources = [{"filename": c["filename"], "product_name": c["product_name"], "model_name": c["model_name"]} for c in chunks]
    prompt = build_prompt(chunks, question)
    client = get_deepseek_client()
    resp = client.chat.completions.create(
        model=settings.deepseek_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=2000,
    )
    answer = _normalize_markdown(resp.choices[0].message.content)
    conv = Conversation(user_id=user_id, question=question, answer=answer, sources=sources, product_id=product_id, model_id=model_id)
    db.add(conv)
    db.commit()
    return {"answer": answer, "sources": sources}

def chat_stream(db: Session, question: str, user_id: int, product_id: int = None, model_id: int = None):
    product_name, model_name = resolve_names(db, product_id, model_id)
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
            yield f"data: {json.dumps(content)}\n\n"
    sources = [{"filename": c["filename"], "product_name": c["product_name"], "model_name": c["model_name"]} for c in chunks]
    conv = Conversation(user_id=user_id, question=question, answer=_normalize_markdown(full_answer), sources=sources, product_id=product_id, model_id=model_id)
    db.add(conv)
    db.commit()
    yield "data: [DONE]\n\n"

def get_conversations(db: Session, user_id: int, role: str, today_only: bool = False) -> list[Conversation]:
    from datetime import datetime, timezone
    q = db.query(Conversation)
    if role != "admin":
        q = q.filter(Conversation.user_id == user_id)
    if today_only:
        now = datetime.now(timezone.utc)
        start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
        q = q.filter(Conversation.created_at >= start)
    return q.order_by(Conversation.created_at.desc()).limit(50).all()

def delete_conversation(db: Session, conv_id: int, user_id: int, role: str):
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="对话不存在")
    if role != "admin" and conv.user_id != user_id:
        raise HTTPException(status_code=403, detail="无权删除此对话")
    db.delete(conv)
    db.commit()
