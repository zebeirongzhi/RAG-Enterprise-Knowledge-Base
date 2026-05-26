from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from database import get_db
from api.deps import get_current_user
from schemas.chat import ChatRequest
from services.chat_service import chat, chat_stream, get_conversations, delete_conversation

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
def list_conversations(db: Session = Depends(get_db), user=Depends(get_current_user), today: bool = False):
    return get_conversations(db, user.id, user.role, today_only=today)

@router.delete("/conversations/{conv_id}")
def remove_conversation(conv_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    delete_conversation(db, conv_id, user.id, user.role)
    return {"detail": "已删除"}
