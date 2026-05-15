from rag.embeddings import get_embedding_model
from rag.ingestion import get_or_create_collection


def search(query: str, product_name: str = "", model_name: str = "", top_k: int = 5) -> list[dict]:
    embed_model = get_embedding_model()
    query_embedding = embed_model.encode(query).tolist()
    collection = get_or_create_collection()

    where = {}
    if model_name:
        where["model_name"] = model_name
    elif product_name:
        where["product_name"] = product_name

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where if where else None,
    )

    chunks = []
    if results["ids"] and results["ids"][0]:
        for i in range(len(results["ids"][0])):
            chunks.append({
                "text": results["documents"][0][i],
                "filename": results["metadatas"][0][i].get("filename", ""),
                "product_name": results["metadatas"][0][i].get("product_name", ""),
                "model_name": results["metadatas"][0][i].get("model_name", ""),
                "score": results["distances"][0][i] if results.get("distances") else 0,
            })
    return chunks
