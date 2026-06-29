from fastapi.testclient import TestClient

from app.main import app


def test_health_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/ai/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "healthcare-compliance-ai",
        "version": "1.0.0",
        "environment": "local",
    }
