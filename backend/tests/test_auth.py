from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

def test_register_requires_admin():
    r = client.post("/api/auth/register", json={"username": "test", "password": "123456", "role": "customer"})
    assert r.status_code == 401  # 无 token

def test_login_invalid_user():
    r = client.post("/api/auth/login", json={"username": "nobody", "password": "wrong"})
    assert r.status_code == 401
