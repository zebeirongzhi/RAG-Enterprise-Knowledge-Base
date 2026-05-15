from pydantic import BaseModel, Field
from datetime import datetime

class UserOut(BaseModel):
    id: int
    username: str
    role: str
    created_at: datetime
    class Config: from_attributes = True

class UserUpdateRole(BaseModel):
    role: str

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(..., min_length=6, max_length=128)
    role: str = "customer"
