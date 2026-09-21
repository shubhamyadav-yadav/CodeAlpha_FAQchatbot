"""
API Integration and Security Tests using FastAPI TestClient.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["indexed_faqs"] >= 15
    assert "similarity_threshold" in data

def test_list_faqs_endpoint():
    response = client.get("/api/v1/faqs")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 15
    assert len(data["categories"]) > 0
    assert len(data["faqs"]) == data["total"]

def test_list_categories_endpoint():
    response = client.get("/api/v1/categories")
    assert response.status_code == 200
    categories = response.json()
    assert "Payment & Billing" in categories
    assert "Account & Security" in categories

def test_chat_valid_query():
    payload = {"question": "What payment methods do you accept?"}
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_fallback"] is False
    assert data["matched_question"] == "What payment methods do you accept?"
    assert data["confidence"] > 0.8
    assert "Visa" in data["answer"]
    assert "response_time_ms" in data

def test_chat_empty_query_rejected():
    payload = {"question": "   "}
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code in (400, 422)

def test_chat_excessive_length_rejected():
    long_question = "How do I pay? " * 100 # > 1000 characters
    payload = {"question": long_question}
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 422

def test_chat_xss_payload_handled_safely():
    payload = {"question": "<script>alert('XSS Attack');</script>"}
    response = client.post("/api/v1/chat", json=payload)
    assert response.status_code == 200
    data = response.json()
    # Should safely return fallback or processed answer without executing
    assert isinstance(data["answer"], str)

def test_security_headers_present():
    response = client.get("/api/v1/health")
    headers = response.headers
    assert headers.get("x-content-type-options") == "nosniff"
    assert headers.get("x-frame-options") == "DENY"
    assert "content-security-policy" in headers
