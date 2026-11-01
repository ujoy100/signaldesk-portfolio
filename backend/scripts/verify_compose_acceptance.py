"""Bounded real-HTTP acceptance checks for the fictional Compose environment."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import httpx
import jwt
from qdrant_client import models
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from backend.app.core.config import get_settings
from backend.app.knowledge.client import create_qdrant_client
from backend.app.models.role import Role
from backend.app.models.ticket import Ticket
from backend.app.models.ticket_event import TicketEvent
from backend.app.models.user import User


def _token(actor_id: int, role: str, *, expired: bool = False) -> str:
    settings = get_settings()
    assert settings.auth_jwt_secret is not None
    return jwt.encode(
        {
            "sub": f"compose-user-{actor_id}",
            "actor_id": actor_id,
            "role": role,
            "aud": settings.auth_jwt_audience,
            "exp": datetime.now(UTC)
            + (timedelta(minutes=-1) if expired else timedelta(minutes=10)),
        },
        settings.auth_jwt_secret.get_secret_value(),
        algorithm="HS256",
    )


def _authorization(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _expect(response: httpx.Response, status: int) -> dict:
    if response.status_code != status:
        raise RuntimeError(
            f"{response.request.method} {response.request.url.path} returned "
            f"{response.status_code}: {response.text[:300]}"
        )
    return response.json()


def main() -> None:
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    with Session(engine) as session:
        identities = dict(
            session.execute(
                select(Role.name, User.id)
                .join(User, User.role_id == Role.id)
                .where(
                    User.email.in_(
                        {
                            "support.agent@example.test",
                            "supervisor@example.test",
                            "admin@example.test",
                        }
                    )
                )
            ).all()
        )
        ticket = session.scalar(
            select(Ticket).where(Ticket.ticket_number == "FIC-TKT-001")
        )
        assert ticket is not None
        ticket_id = ticket.id
        events_before = session.scalar(
            select(func.count())
            .select_from(TicketEvent)
            .where(
                TicketEvent.ticket_id == ticket_id,
                TicketEvent.event_type == "approved_update",
            )
        )

    agent = _token(identities["support_agent"], "support_agent")
    supervisor = _token(identities["supervisor"], "supervisor")
    admin = _token(identities["admin"], "admin")
    base = "http://127.0.0.1:8000"
    results: dict[str, object] = {}

    with httpx.Client(base_url=base, timeout=30) as client:
        session_view = _expect(
            client.get("/api/v1/session", headers=_authorization(agent)), 200
        )
        results["session_role"] = session_view["role"]
        results["invalid_token_status"] = client.get(
            "/api/v1/session", headers=_authorization("not-a-token")
        ).status_code
        results["expired_token_status"] = client.get(
            "/api/v1/session",
            headers=_authorization(
                _token(identities["support_agent"], "support_agent", expired=True)
            ),
        ).status_code

        sim = _expect(
            client.post(
                "/api/v1/support/issues",
                headers=_authorization(agent),
                json={"issue": "How do I activate my fictional SIM?"},
            ),
            200,
        )
        assert sim["workflow_mode"] == "deterministic"
        assert sim["resolution"] and sim["resolution"]["evidence"]
        results["sim_evidence_count"] = len(sim["resolution"]["evidence"])

        proposed = _expect(
            client.post(
                "/api/v1/support/issues",
                headers=_authorization(agent),
                json={
                    "issue": "Apply the cited SIM activation guidance and resolve this ticket",
                    "ticket_id": ticket_id,
                    "propose_ticket_update": True,
                },
            ),
            200,
        )
        assert proposed["status"] == "approval_pending"
        approval_id = proposed["approval_id"]
        results["unauthorized_approval_status"] = client.post(
            f"/api/v1/approvals/{approval_id}/decisions",
            headers=_authorization(agent),
            json={"decision": "approve"},
        ).status_code
        edited = _expect(
            client.post(
                f"/api/v1/approvals/{approval_id}/decisions",
                headers=_authorization(supervisor),
                json={
                    "decision": "edit",
                    "edited_action": {
                        "operation": "update_ticket",
                        "payload": {
                            "ticket_id": ticket_id,
                            "status": "resolved",
                            "priority": "high",
                        },
                    },
                    "note": "Material priority edit requires reauthorization.",
                },
            ),
            200,
        )
        replacement_id = edited["approval_id"]
        completed = _expect(
            client.post(
                f"/api/v1/approvals/{replacement_id}/decisions",
                headers=_authorization(supervisor),
                json={"decision": "approve"},
            ),
            200,
        )
        assert completed["status"] == "completed"
        results["edit_reauthorized"] = replacement_id != approval_id

        feedback = _expect(
            client.post(
                "/api/v1/feedback",
                headers=_authorization(agent),
                json={
                    "thread_id": sim["thread_id"],
                    "rating": 5,
                    "comment": "Fictional activation answer was grounded and clear.",
                },
            ),
            201,
        )
        history = _expect(
            client.get("/api/v1/feedback", headers=_authorization(supervisor)), 200
        )
        results["feedback_visible"] = any(
            item["id"] == feedback["id"] for item in history
        )

        suffix = uuid4().hex[:12]
        uploaded = _expect(
            client.post(
                "/api/v1/knowledge/versions",
                headers=_authorization(admin),
                json={
                    "version": "1.0",
                    "media_type": "text/markdown",
                    "content": "Fictional Compose acceptance policy for safe SIM activation and testing.",
                    "metadata": {
                        "document_id": f"compose-policy-{suffix}",
                        "source": f"fictional://compose/{suffix}",
                        "service": "mobile",
                        "category": "activation",
                        "version": "1.0",
                        "active": False,
                        "access_roles": ["public"],
                        "page": 1,
                        "section": "Acceptance",
                        "title": "Compose acceptance policy",
                    },
                },
            ),
            201,
        )
        requested = _expect(
            client.post(
                f"/api/v1/knowledge/versions/{uploaded['version_id']}/promotion-requests",
                headers=_authorization(admin),
                json={"thread_id": f"compose-knowledge-{uuid4()}"},
            ),
            201,
        )
        _expect(
            client.post(
                f"/api/v1/knowledge/promotion-approvals/{requested['approval_id']}/decisions",
                headers=_authorization(supervisor),
                json={"decision": "approve"},
            ),
            200,
        )
        promoted = _expect(
            client.post(
                f"/api/v1/knowledge/versions/{uploaded['version_id']}/promote",
                headers=_authorization(supervisor),
                json={
                    "approval_id": requested["approval_id"],
                    "execution_request_id": f"compose-execution-{uuid4()}",
                },
            ),
            200,
        )
        assert promoted["status"] == "active"
        qdrant = create_qdrant_client(settings)
        points, _ = qdrant.scroll(
            settings.qdrant_collection,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(value=f"compose-policy-{suffix}"),
                    ),
                    models.FieldCondition(
                        key="active", match=models.MatchValue(value=True)
                    ),
                ]
            ),
            limit=10,
            with_payload=True,
        )
        results["promoted_qdrant_points"] = len(points)

    with Session(engine) as session:
        refreshed = session.get(Ticket, ticket_id)
        events_after = session.scalar(
            select(func.count())
            .select_from(TicketEvent)
            .where(
                TicketEvent.ticket_id == ticket_id,
                TicketEvent.event_type == "approved_update",
            )
        )
        results["ticket_status"] = refreshed.status if refreshed else None
        results["exactly_once_event_delta"] = events_after - events_before
    engine.dispose()

    assert results["invalid_token_status"] == 401
    assert results["expired_token_status"] == 401
    assert results["unauthorized_approval_status"] == 403
    assert results["edit_reauthorized"] is True
    assert results["feedback_visible"] is True
    assert results["promoted_qdrant_points"] == 1
    assert results["ticket_status"] == "resolved"
    assert results["exactly_once_event_delta"] == 1
    print(results)


if __name__ == "__main__":
    main()
