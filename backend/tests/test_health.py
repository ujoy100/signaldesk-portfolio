from fastapi.testclient import TestClient

from backend.app.main import create_app


def test_health_returns_200():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_ready_returns_200():
    client = TestClient(create_app())

    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {"application": "ok"},
    }


def test_health_response_schema():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.headers["content-type"] == "application/json"
    assert isinstance(response.json()["status"], str)


def test_health_routes_in_openapi():
    client = TestClient(create_app())

    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "/health" in paths
    assert "/ready" in paths


def test_readiness_returns_503_when_application_not_ready():
    """Readiness must fail when the application is marked not ready."""

    app = create_app()
    app.state.is_ready = False

    client = TestClient(app)

    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "not_ready",
        "checks": {"application": "not_ready"},
    }


def test_health_remains_healthy_when_application_not_ready():
    """Liveness and readiness represent different conditions."""

    app = create_app()
    app.state.is_ready = False

    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
