import pytest
from fastapi.testclient import TestClient
from main import app
from config import Settings, get_settings

client = TestClient(app)

def get_settings_override():
    return Settings(
        gemini_api_key="fake-key-for-testing",
        tavily_api_key="fake-key-for-testing",
        mongodb_uri="",  # Disable DB for pure API tests
    )

app.dependency_overrides[get_settings] = get_settings_override


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["service"] == "CloudCompare API"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    
    # Since DB is disabled in override, it should be disconnected
    assert data["database"] == "disconnected"
    assert data["gemini"] == "configured"
    assert data["tavily"] == "configured"
