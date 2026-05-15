from pydantic import BaseModel
from datetime import datetime

class ModelCreate(BaseModel):
    product_id: int
    name: str
    description: str = ""

class ModelOut(BaseModel):
    id: int
    product_id: int
    name: str
    description: str
    created_at: datetime

    class Config:
        from_attributes = True
