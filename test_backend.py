"""
FastAPI Backend Integration Test Suite
Verifies backend routes, health check responses, configuration loading, and database connectivity.
"""

from fastapi.testclient import TestClient
from backend.main import app
from backend.config import get_settings

client = TestClient(app)


def test_root_endpoint():
    """Verify root GET / endpoint returns 200 and valid JSON."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "app" in data
    assert "version" in data
    print("✅ test_root_endpoint passed")


def test_health_endpoint():
    """Verify /health endpoint returns structured health status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "degraded")
    assert "app_name" in data
    assert "version" in data
    assert "database" in data
    assert data["database"]["healthy"] is True
    assert data["database"]["status"] == "connected"
    print("✅ test_health_endpoint passed")


def test_v1_health_endpoint():
    """Verify /api/v1/health prefix endpoint works properly."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "degraded")
    assert data["database"]["healthy"] is True
    print("✅ test_v1_health_endpoint passed")


def test_config_singleton():
    """Verify settings singleton loads without exposing secrets."""
    settings = get_settings()
    assert settings.app_name == "ZeroSQL AI V2 API"
    assert settings.effective_readonly_db_url is not None
    print("✅ test_config_singleton passed")


if __name__ == "__main__":
    print("===============================================================")
    print("  FASTAPI BACKEND VERIFICATION TEST SUITE")
    print("===============================================================\n")
    test_root_endpoint()
    test_health_endpoint()
    test_v1_health_endpoint()
    test_config_singleton()
    print("\n===============================================================")
    print("  🎉 ALL FASTAPI BACKEND TESTS PASSED WITH 100% SUCCESS!")
    print("===============================================================")
