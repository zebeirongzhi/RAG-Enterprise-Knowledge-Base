from pydantic import BaseModel
from datetime import datetime

class DocumentOut(BaseModel):
    id: int
    model_id: int
    filename: str
    file_type: str
    file_size: int
    status: str
    chunk_count: int
    created_at: datetime

    class Config:
        from_attributes = True

class DocumentStatus(BaseModel):
    id: int
    status: str
    chunk_count: int
