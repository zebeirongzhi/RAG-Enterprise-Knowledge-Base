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
