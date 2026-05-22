from sentence_transformers import SentenceTransformer
from config import settings

_embedding_model = None


def get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(
            settings.embedding_model,
            device=settings.embedding_device,
            local_files_only=True
        )
    return _embedding_model
