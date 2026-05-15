from pydantic import BaseModel

class ChatRequest(BaseModel):
    question: str
    product_id: int | None = None
    model_id: int | None = None
    product_name: str = ""
    model_name: str = ""
