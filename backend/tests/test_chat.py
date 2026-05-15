from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_chat_requires_auth():
    r = client.post("/api/chat/ask", json={"question": "测试"})
    assert r.status_code == 401

def test_conversations_requires_auth():
    r = client.get("/api/chat/conversations")
    assert r.status_code == 401
