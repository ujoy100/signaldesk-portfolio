from fastapi.testclient import TestClient

from backend.app.core.config import Settings
from backend.app.main import create_app


def create_test_client() -> TestClient:
    """Create an isolated application with explicit test settings."""
    settings = Settings(
        _env_file=None,
        app_env="testing",
        cors_origins=["http://localhost:5173"],
    )

    return TestClient(create_app(settings=settings))


def test_allowed_origin():
    client = create_test_client()

    response = client.get(
        "/health",
        headers={"Origin": "http://localhost:5173"},
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_disallowed_origin():
    client = create_test_client()

    response = client.get(
        "/health",
        headers={"Origin": "http://untrusted.example"},
    )

    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_allowed_get_preflight():
    client = create_test_client()

    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "GET" in response.headers["access-control-allow-methods"]


def test_allowed_post_preflight():
    """Allow POST preflight requests from the configured frontend."""

    client = create_test_client()

    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == ("http://localhost:5173")


def test_disallowed_delete_preflight():
    """Reject DELETE preflight requests."""

    client = create_test_client()

    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "DELETE",
        },
    )

    assert response.status_code == 400
