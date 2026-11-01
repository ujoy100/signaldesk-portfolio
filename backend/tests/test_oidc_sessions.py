"""OIDC transaction and revocable server-session security tests."""

import hashlib
import logging
from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Connection, select
from sqlalchemy.orm import Session

from backend.app.core.config import Settings
from backend.app.core.oidc import (
    OIDCError,
    authenticate_session,
    begin_login,
    redeem_code,
    revoke_session,
)
from backend.app.main import create_app
from backend.app.models.auth_session import AuthSession
from backend.app.models.external_identity import ExternalIdentity
from backend.app.models.oidc_login import OIDCLogin
from backend.app.models.role import Role
from backend.app.models.user import User


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def test_login_transaction_uses_state_nonce_and_pkce(
    test_db_connection: Connection,
) -> None:
    settings = Settings(
        _env_file=None,
        entra_tenant_id="fictional-tenant",
        entra_client_id="fictional-client",
        entra_client_secret="not-a-real-secret",
    )
    session = Session(bind=test_db_connection, join_transaction_mode="create_savepoint")
    url = urlparse(begin_login(session, settings))
    query = parse_qs(url.query)
    assert url.netloc == "login.microsoftonline.com"
    assert query["code_challenge_method"] == ["S256"]
    assert query["state"][0] != query["nonce"][0]
    assert len(query["code_challenge"][0]) >= 43
    session.close()


def test_session_requires_csrf_and_supports_revocation(
    test_db_connection: Connection,
) -> None:
    session = Session(bind=test_db_connection, join_transaction_mode="create_savepoint")
    role = Role(name="oidc_test_agent", description="test")
    session.add(role)
    session.flush()
    user = User(
        email="oidc-session@example.invalid",
        full_name="Fictional Session User",
        role_id=role.id,
    )
    session.add(user)
    session.flush()
    raw, csrf = "fictional-session-token", "fictional-csrf-token"
    session.add(
        AuthSession(
            user_id=user.id,
            token_hash=_hash(raw),
            csrf_hash=_hash(csrf),
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
        )
    )
    session.commit()
    assert authenticate_session(session, raw, csrf, require_csrf=True) == (
        user.id,
        "oidc_test_agent",
    )
    with pytest.raises(OIDCError, match="Invalid or expired"):
        authenticate_session(session, raw, "forged", require_csrf=True)
    revoke_session(session, raw)
    with pytest.raises(OIDCError, match="Invalid or expired"):
        authenticate_session(session, raw, csrf, require_csrf=False)
    session.close()


def test_code_redemption_maps_identity_and_is_single_use(
    test_db_connection: Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = Settings(
        _env_file=None,
        entra_tenant_id="fictional-tenant",
        entra_client_id="fictional-client",
        entra_client_secret="not-a-real-secret",
    )
    session = Session(bind=test_db_connection, join_transaction_mode="create_savepoint")
    role = Role(name="oidc_redeem_agent", description="test")
    session.add(role)
    session.flush()
    user = User(
        email="oidc-redeem@example.invalid",
        full_name="Fictional Entra User",
        role_id=role.id,
    )
    session.add(user)
    session.flush()
    session.add(
        ExternalIdentity(
            user_id=user.id,
            provider="entra",
            tenant_id="fictional-tenant",
            subject="fictional-subject",
        )
    )
    session.add(
        OIDCLogin(
            state_hash=_hash("state"),
            nonce="nonce",
            code_verifier="verifier",
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
        )
    )
    session.commit()

    class Response:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, str]:
            return {"id_token": "header.payload.signature"}

    class Key:
        key = "fictional-public-key"

    class JWKClient:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

        def get_signing_key_from_jwt(self, _token: str) -> Key:
            return Key()

    monkeypatch.setattr(
        "backend.app.core.oidc.httpx.post", lambda *_args, **_kwargs: Response()
    )
    monkeypatch.setattr("backend.app.core.oidc.jwt.PyJWKClient", JWKClient)
    monkeypatch.setattr(
        "backend.app.core.oidc.jwt.decode",
        lambda *_args, **_kwargs: {
            "sub": "fictional-subject",
            "oid": "fictional-subject",
            "tid": "fictional-tenant",
            "nonce": "nonce",
            "exp": 9999999999,
            "iss": "validated",
            "aud": "fictional-client",
            "name": "Verified Fictional Person",
        },
    )
    raw, csrf = redeem_code(session, settings, state="state", code="fictional-code")
    assert authenticate_session(session, raw, csrf, require_csrf=True) == (
        user.id,
        "oidc_redeem_agent",
    )
    persisted = session.scalar(
        select(AuthSession).where(AuthSession.token_hash == _hash(raw))
    )
    assert persisted is not None
    assert persisted.display_name == "Verified Fictional Person"
    with pytest.raises(OIDCError, match="state"):
        redeem_code(session, settings, state="state", code="replay")
    session.close()


def test_missing_verified_name_uses_safe_fallback(
    test_db_connection: Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings = Settings(
        _env_file=None,
        entra_tenant_id="fictional-tenant",
        entra_client_id="fictional-client",
        entra_client_secret="not-a-real-secret",
    )
    session = Session(bind=test_db_connection, join_transaction_mode="create_savepoint")
    role = Role(name="oidc_fallback_agent", description="test")
    session.add(role)
    session.flush()
    user = User(
        email="oidc-fallback@example.invalid",
        full_name="Database Name Must Not Leak",
        role_id=role.id,
    )
    session.add(user)
    session.flush()
    session.add(
        ExternalIdentity(
            user_id=user.id,
            provider="entra",
            tenant_id="fictional-tenant",
            subject="fallback-subject",
        )
    )
    session.add(
        OIDCLogin(
            state_hash=_hash("fallback-state"),
            nonce="fallback-nonce",
            code_verifier="fallback-verifier",
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
        )
    )
    session.commit()

    class Response:
        def raise_for_status(self) -> None:
            pass

        def json(self) -> dict[str, str]:
            return {"id_token": "header.payload.signature"}

    class Key:
        key = "fictional-public-key"

    class JWKClient:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

        def get_signing_key_from_jwt(self, _token: str) -> Key:
            return Key()

    monkeypatch.setattr(
        "backend.app.core.oidc.httpx.post", lambda *_a, **_k: Response()
    )
    monkeypatch.setattr("backend.app.core.oidc.jwt.PyJWKClient", JWKClient)
    monkeypatch.setattr(
        "backend.app.core.oidc.jwt.decode",
        lambda *_a, **_k: {
            "sub": "fallback-subject",
            "oid": "fallback-subject",
            "tid": "fictional-tenant",
            "nonce": "fallback-nonce",
            "exp": 9999999999,
            "iss": "validated",
            "aud": "fictional-client",
        },
    )
    raw, _csrf = redeem_code(
        session, settings, state="fallback-state", code="fictional-code"
    )
    persisted = session.scalar(
        select(AuthSession).where(AuthSession.token_hash == _hash(raw))
    )
    assert persisted is not None
    assert persisted.display_name == "Microsoft user"
    session.close()


def test_code_exchange_logs_only_safe_failure_metadata(
    test_db_connection: Connection,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    session = Session(bind=test_db_connection, join_transaction_mode="create_savepoint")
    session.add(
        OIDCLogin(
            state_hash=_hash("safe-state"),
            nonce="sensitive-nonce",
            code_verifier="sensitive-verifier",
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
        )
    )
    session.commit()
    response = httpx.Response(
        401,
        json={
            "error": "invalid_client",
            "error_description": "AADSTS7000215: invalid client secret",
        },
        request=httpx.Request("POST", "https://example.invalid/token"),
    )
    monkeypatch.setattr("backend.app.core.oidc.httpx.post", lambda *_a, **_k: response)
    settings = Settings(
        _env_file=None,
        entra_tenant_id="fictional-tenant",
        entra_client_id="fictional-client",
        entra_client_secret="sensitive-client-secret",
    )
    with caplog.at_level(logging.WARNING), pytest.raises(OIDCError):
        redeem_code(session, settings, state="safe-state", code="sensitive-auth-code")
    record = caplog.records[-1]
    assert record.oidc_stage == "authorization_code_exchange"
    assert record.provider_error == "invalid_client"
    assert record.provider_code == "AADSTS7000215"
    assert "sensitive" not in caplog.text
    session.close()


def test_production_rejects_development_bearer_tokens() -> None:
    app = create_app(
        Settings(
            _env_file=None,
            app_env="production",
            cookie_secure=True,
            auth_jwt_secret="test-only-secret-with-sufficient-entropy",
        )
    )
    response = TestClient(app).get(
        "/api/v1/session", headers={"Authorization": "Bearer fictional"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Bearer development access disabled"
