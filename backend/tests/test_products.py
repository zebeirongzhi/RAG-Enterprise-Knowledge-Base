from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_get_products_requires_auth():
    r = client.get("/api/products")
    assert r.status_code == 401

def test_create_product_requires_admin():
    r = client.post("/api/products", json={"name": "Test", "description": "Test"})
    assert r.status_code == 401
