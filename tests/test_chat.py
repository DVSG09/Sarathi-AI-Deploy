import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_chat_faq():
    r = client.post("/api/v1/chat", json={"user_id": "u1", "message": "What is the refund policy?"})
    assert r.status_code == 200
    data = r.json()
    assert "Refunds are eligible" in data["reply"]

def test_chat_status_no_id():
    r = client.post("/api/v1/chat", json={"user_id": "u1", "message": "status please"})
    assert r.status_code == 200
    assert "Order ID" in r.json()["reply"]

def test_chat_status_with_id():
    r = client.post("/api/v1/chat", json={"user_id": "u1", "message": "Where is my order ORD123?"})
    assert r.status_code == 200
    assert "Order ORD123" in r.json()["reply"]
