from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_list_docs_requires_auth():
    r = client.get("/api/models/1/docs")
    assert r.status_code == 401
