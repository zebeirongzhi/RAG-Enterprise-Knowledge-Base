from pydantic import BaseModel
from datetime import datetime

class ProductCreate(BaseModel):
    name: str
    description: str = ""

class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

class ProductOut(BaseModel):
    id: int
    name: str
    description: str
    created_at: datetime

    class Config:
        from_attributes = True
