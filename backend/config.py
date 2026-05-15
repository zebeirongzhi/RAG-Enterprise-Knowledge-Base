# D:\RAG\backend\config.py
import os
from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    # 数据库
    database_url: str = "sqlite:///./kb.db"

    @field_validator("database_url")
    @classmethod
    def resolve_db_path(cls, v: str) -> str:
        if v.startswith("sqlite:///") and not v.startswith("sqlite:////"):
            path = v.removeprefix("sqlite:///")
            if not os.path.isabs(path):
                abs_path = os.path.normpath(os.path.join(os.path.dirname(__file__), path))
                return f"sqlite:///{abs_path}"
        return v

    @field_validator("chroma_persist_dir", "upload_dir")
    @classmethod
    def resolve_path(cls, v: str) -> str:
        if not os.path.isabs(v):
            return os.path.normpath(os.path.join(os.path.dirname(__file__), v))
        return v

    # JWT
    secret_key: str = "change-me-in-production-use-a-strong-random-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    # DeepSeek
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # Embedding
    embedding_model: str = "BAAI/bge-large-zh-v1.5"
    embedding_device: str = "cpu"

    # ChromaDB
    chroma_persist_dir: str = "./chroma_data"

    # Upload
    upload_dir: str = "./uploads"
    max_upload_size_mb: int = 50

    # OCR
    enable_ocr: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
