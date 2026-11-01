"""Authentication boundary tests."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest

from backend.app.core.auth import AuthenticationError, authenticate_bearer_token
from backend.app.core.config import Settings


def _settings() -> Settings:
    return Settings(
        _env_file=None,
        auth_jwt_secret="test-only-secret-with-sufficient-entropy",
        auth_jwt_audience="telecom-tests",
    )


def issue_token(*, role: str = "support_agent") -> str:
    settings = _settings()
    return jwt.encode(
        {
            "sub": "fictional-user",
            "actor_id": 42,
            "role": role,
            "aud": settings.auth_jwt_audience,
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        settings.auth_jwt_secret.get_secret_value(),
        algorithm="HS256",
    )


def test_valid_token_returns_typed_principal() -> None:
    principal = authenticate_bearer_token(issue_token(), _settings())

    assert principal.subject == "fictional-user"
    assert principal.actor_id == 42
    assert principal.role == "support_agent"


def test_authentication_fails_closed_without_secret() -> None:
    with pytest.raises(AuthenticationError, match="not configured"):
        authenticate_bearer_token(
            "untrusted", Settings(_env_file=None, auth_jwt_secret=None)
        )


def test_authentication_rejects_invalid_token() -> None:
    with pytest.raises(AuthenticationError, match="Invalid"):
        authenticate_bearer_token("untrusted", _settings())
