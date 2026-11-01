"""API-level Entra session revocation, CSRF, cookie, and RBAC tests."""

import hashlib
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.api.routes import auth as auth_routes
from backend.app.api.routes.knowledge_admin import get_lifecycle_service
from backend.app.api.routes.support import get_support_db, get_workflow
from backend.app.core.config import Settings
from backend.app.main import create_app
from backend.app.models.auth_session import AuthSession
from backend.app.models.external_identity import ExternalIdentity
from backend.app.models.human_approval import HumanApproval
from backend.app.models.knowledge_version import KnowledgeVersion
from backend.app.models.role import Role
from backend.app.models.user import User
from backend.app.services.knowledge_lifecycle import KnowledgeAuthorizationError

_TEST_ROLE_DESCRIPTION = "CI-only role created by Entra session tests"


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


class _DeniedLifecycle:
    def __init__(self, session: Session) -> None:
        self.session = session

    def upload(self, *_args: object, **_kwargs: object) -> None:
        raise KnowledgeAuthorizationError("Admin role required")

    def deactivate(self, *_args: object, **_kwargs: object) -> None:
        raise KnowledgeAuthorizationError("Admin role required")


class _PermittedGraph:
    async def ainvoke(self, _state: dict, _config: dict) -> dict:
        return {
            "status": "completed",
            "complexity": "simple",
            "resolution": {
                "issue_type": "sim_activation",
                "likely_cause": "Fictional activation is still provisioning.",
                "evidence": [],
                "confidence": 0.8,
                "next_steps": ["Restart the fictional device."],
                "action_required": False,
                "requires_human_approval": False,
                "ticket_draft": None,
                "insufficient_evidence": False,
            },
        }


class _PermittedWorkflow:
    graph = _PermittedGraph()


def _session_app(test_db_engine, *, expired: bool = False):
    factory = sessionmaker(bind=test_db_engine, expire_on_commit=False)
    raw = f"fictional-session-{uuid4()}"
    csrf = f"fictional-csrf-{uuid4()}"
    with factory() as session:
        role = session.scalar(select(Role).where(Role.name == "support_agent"))
        if role is None:
            role = Role(
                name="support_agent",
                description=_TEST_ROLE_DESCRIPTION,
            )
            session.add(role)
            session.flush()
        user = User(
            email=f"entra-api-{uuid4()}@example.invalid",
            full_name="Fictional Entra Support Agent",
            role_id=role.id,
        )
        session.add(user)
        session.flush()
        identity = ExternalIdentity(
            user_id=user.id,
            provider="entra",
            tenant_id="fictional-tenant",
            subject=f"fictional-object-{uuid4()}",
        )
        session.add(identity)
        session.add(
            AuthSession(
                user_id=user.id,
                token_hash=_hash(raw),
                csrf_hash=_hash(csrf),
                expires_at=datetime.now(UTC)
                + (timedelta(minutes=-1) if expired else timedelta(minutes=5)),
            )
        )
        session.commit()
        user_id = user.id

    def override_db() -> Iterator[Session]:
        with factory() as session:
            yield session

    app = create_app(
        Settings(
            _env_file=None,
            app_env="production",
            cookie_secure=True,
            database_url=test_db_engine.url.render_as_string(hide_password=False),
        )
    )
    app.dependency_overrides[get_support_db] = override_db
    app.dependency_overrides[get_workflow] = lambda: _PermittedWorkflow()

    def override_lifecycle() -> Iterator[_DeniedLifecycle]:
        with factory() as session:
            yield _DeniedLifecycle(session)

    app.dependency_overrides[get_lifecycle_service] = override_lifecycle
    client = TestClient(app, base_url="https://testserver")
    client.cookies.set("signaldesk_session", raw)
    client.cookies.set("signaldesk_csrf", csrf)
    return app, client, factory, user_id, raw, csrf


def _cleanup(factory, user_id: int) -> None:
    with factory() as session, session.begin():
        session.execute(delete(AuthSession).where(AuthSession.user_id == user_id))
        session.execute(
            delete(ExternalIdentity).where(ExternalIdentity.user_id == user_id)
        )
        session.execute(delete(User).where(User.id == user_id))
        role = session.scalar(
            select(Role).where(
                Role.name == "support_agent",
                Role.description == _TEST_ROLE_DESCRIPTION,
            )
        )
        if role is not None:
            session.delete(role)


def test_logout_revokes_server_session_and_replay_fails(test_db_engine) -> None:
    _app, client, factory, user_id, raw, csrf = _session_app(test_db_engine)
    try:
        assert client.get("/api/v1/session").status_code == 200
        response = client.post("/auth/logout", headers={"X-CSRF-Token": csrf})
        assert response.status_code == 204
        cookies = response.headers.get_list("set-cookie")
        assert any(
            "signaldesk_session=" in item and "HttpOnly" in item for item in cookies
        )
        assert all("Secure" in item and "SameSite=lax" in item for item in cookies)
        with factory() as session:
            record = session.scalar(
                select(AuthSession).where(AuthSession.user_id == user_id)
            )
            assert record is not None and record.revoked_at is not None
        replay = TestClient(client.app, base_url="https://testserver")
        replay.cookies.set("signaldesk_session", raw)
        assert replay.get("/api/v1/session").status_code == 401
    finally:
        _cleanup(factory, user_id)


def test_session_csrf_expiry_and_support_agent_rbac(test_db_engine) -> None:
    _app, client, factory, user_id, _raw, csrf = _session_app(test_db_engine)
    try:
        with factory() as session:
            approvals_before = session.scalar(select(func.count(HumanApproval.id)))
            versions_before = session.scalar(select(func.count(KnowledgeVersion.id)))

        assert client.get("/api/v1/session").json() == {
            "actor_id": user_id,
            "role": "support_agent",
            "display_name": "Microsoft user",
        }
        permitted = client.post(
            "/api/v1/support/issues",
            headers={"X-CSRF-Token": csrf},
            json={"issue": "How do I activate my fictional SIM?"},
        )
        assert permitted.status_code == 200
        assert permitted.json()["workflow_mode"] == "deterministic"
        assert client.get("/api/v1/approvals").status_code == 403
        assert client.get("/api/v1/approvals/999999").status_code == 403
        denied_ticket_decision = client.post(
            "/api/v1/approvals/999999/decisions",
            headers={"X-CSRF-Token": csrf},
            json={"decision": "approve"},
        )
        assert denied_ticket_decision.status_code == 403

        missing_csrf = client.post(
            "/api/v1/knowledge/versions/999999/promotion-requests",
            json={"thread_id": "fictional-thread"},
        )
        assert missing_csrf.status_code == 401
        denied_promotion = client.post(
            "/api/v1/knowledge/versions/999999/promotion-requests",
            headers={"X-CSRF-Token": csrf},
            json={"thread_id": "fictional-thread"},
        )
        assert denied_promotion.status_code == 403
        denied_decision = client.post(
            "/api/v1/knowledge/promotion-approvals/999999/decisions",
            headers={"X-CSRF-Token": csrf},
            json={"decision": "approve"},
        )
        assert denied_decision.status_code == 403
        denied_upload = client.post(
            "/api/v1/knowledge/versions",
            headers={"X-CSRF-Token": csrf},
            json={
                "version": "1.0",
                "media_type": "text/plain",
                "content": "Fictional unauthorized content long enough for validation.",
                "metadata": {
                    "document_id": "unauthorized-test",
                    "source": "fictional://unauthorized",
                    "service": "mobile",
                    "category": "test",
                    "version": "1.0",
                    "active": False,
                    "access_roles": ["public"],
                    "page": 1,
                    "section": "Test",
                    "title": "Unauthorized test",
                },
            },
        )
        assert denied_upload.status_code == 403
        denied_deactivation = client.post(
            "/api/v1/knowledge/versions/999999/deactivate",
            headers={"X-CSRF-Token": csrf},
            json={"reason": "Unauthorized support-agent request"},
        )
        assert denied_deactivation.status_code == 403

        with factory() as session:
            assert (
                session.scalar(select(func.count(HumanApproval.id))) == approvals_before
            )
            assert (
                session.scalar(select(func.count(KnowledgeVersion.id)))
                == versions_before
            )
            mapping = session.scalar(
                select(ExternalIdentity).where(ExternalIdentity.user_id == user_id)
            )
            user = session.get(User, user_id)
            assert mapping is not None and not hasattr(mapping, "role_id")
            assert user is not None and user.role_id is not None
            auth_record = session.scalar(
                select(AuthSession).where(AuthSession.user_id == user_id)
            )
            assert auth_record is not None and auth_record.revoked_at is None
    finally:
        _cleanup(factory, user_id)

    _app, expired_client, expired_factory, expired_user, *_ = _session_app(
        test_db_engine, expired=True
    )
    try:
        assert expired_client.get("/api/v1/session").status_code == 401
    finally:
        _cleanup(expired_factory, expired_user)


def test_production_callback_cookie_attributes(monkeypatch) -> None:
    settings = Settings(_env_file=None, app_env="production", cookie_secure=True)
    app = create_app(settings)
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/auth/callback",
            "headers": [],
            "query_string": b"",
            "server": ("testserver", 443),
            "scheme": "https",
            "app": app,
        }
    )
    monkeypatch.setattr(
        auth_routes, "redeem_code", lambda *_args, **_kwargs: ("session", "csrf")
    )
    response = auth_routes.callback(request, None, "state", "code")  # type: ignore[arg-type]
    cookies = response.headers.getlist("set-cookie")
    session_cookie = next(
        item for item in cookies if item.startswith("signaldesk_session")
    )
    assert "HttpOnly" in session_cookie
    assert "Secure" in session_cookie
    assert "SameSite=lax" in session_cookie


def test_openapi_expands_lazy_included_routers() -> None:
    app = create_app(Settings(_env_file=None, app_env="testing"))
    assert any(type(route).__name__ == "_IncludedRouter" for route in app.routes)
    paths = app.openapi()["paths"]
    assert "/auth/logout" in paths
    assert "/api/v1/session" in paths
    assert "/api/v1/approvals" in paths
    assert "/api/v1/knowledge/versions/{version_id}/promote" in paths
