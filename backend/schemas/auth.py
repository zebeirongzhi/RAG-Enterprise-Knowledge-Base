from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="用户名，仅支持字母、数字、下划线，3-50 个字符",
    )
    password: str = Field(
        ...,
        min_length=6,
        max_length=128,
        description="密码，6-128 个字符",
    )
    role: str = "customer"

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
