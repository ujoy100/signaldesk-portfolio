"""Authenticated FastAPI integration tests for support and approval routes."""

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from fastapi.testclient import TestClient
from langgraph.checkpoint.memory import InMemorySaver
from sqlalchemy import Connection, select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.api.routes.support import get_support_db, get_workflow
from backend.app.core.config import Settings
from backend.app.knowledge.models import Evidence, RetrievalResponse
from backend.app.main import create_app
from backend.app.mcp.contracts import GatewayResponse
from backend.app.models.customer import Customer
from backend.app.models.role import Role
from backend.app.models.subscription import Subscription  # noqa: F401
from backend.app.models.ticket import Ticket
from backend.app.models.user import User
from backend.app.workflow.graph import SupportWorkflow

SECRET = "test-only-support-api-secret-with-sufficient-entropy"
AUDIENCE = "support-api-tests"


class ApiRetriever:
    def retrieve(self, query: str, **kwargs: object) -> RetrievalResponse:
        return RetrievalResponse(
            answered=True,
            strategy="hybrid_reranked",
            evidence=[
                Evidence(
                    chunk_id="api-chunk",
                    document_id="api-guide",
                    source="fictional",
                    title="API guide",
                    section="activation",
                    page=1,
                    version="1.0",
                    service="mobile",
                    category="activation",
                    content="Restart after activating the fictional SIM.",
                    score=0.9,
                    retrieval_signals=["test"],
                )
            ],
        )


class ApiGateway:
    async def invoke(
        self,
        namespace: str,
        tool: str,
        arguments: dict,
        principal: object,
        **kwargs: object,
    ) -> GatewayResponse:
        if tool == "get_ticket_history":
            result = {"ticket_id": arguments["ticket_id"], "events": []}
        else:
            result = {"executed": True, "code": "executed", "message": "test"}
        return GatewayResponse(
            request_id=str(uuid4()),
            namespace=namespace,
            tool=tool,
            allowed=True,
            result=result,
        )


def _token(actor_id: int, role: str, *, expired: bool = False) -> str:
    return jwt.encode(
        {
            "sub": f"user-{actor_id}",
            "actor_id": actor_id,
            "role": role,
            "aud": AUDIENCE,
            "exp": datetime.now(UTC)
            + (timedelta(minutes=-1) if expired else timedelta(minutes=5)),
        },
        SECRET,
        algorithm="HS256",
    )


def _user(session: Session, role_name: str) -> User:
    role = session.scalar(select(Role).where(Role.name == role_name))
    if role is None:
        role = Role(name=role_name, description="API test")
        session.add(role)
        session.flush()
    suffix = uuid4().hex[:8]
    user = User(
        email=f"api-{suffix}@example.test",
        full_name="API Test User",
        role_id=role.id,
    )
    session.add(user)
    session.flush()
    return user


def test_authenticated_submission_and_approval_role_boundaries(
    test_db_connection: Connection,
) -> None:
    factory = sessionmaker(
        bind=test_db_connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )
    with factory() as session:
        agent = _user(session, "support_agent")
        supervisor = _user(session, "supervisor")
        admin = _user(session, "admin")
        customer_role = Role(name=f"customer-{uuid4().hex[:8]}")
        session.add(customer_role)
        session.flush()
        unsupported = User(
            email=f"unsupported-{uuid4().hex[:8]}@example.test",
            full_name="Unsupported",
            role_id=customer_role.id,
        )
        session.add(unsupported)
        customer = Customer(
            customer_number=f"API-{uuid4().hex[:8]}", full_name="Fictional API Customer"
        )
        session.add(customer)
        session.flush()
        ticket = Ticket(
            ticket_number=f"API-TKT-{uuid4().hex[:8]}",
            customer_id=customer.id,
            subject="API approval",
            description="Fictional ticket",
        )
        session.add(ticket)
        session.commit()
        agent_id, supervisor_id, admin_id = agent.id, supervisor.id, admin.id
        unsupported_id, ticket_id = unsupported.id, ticket.id

    workflow = SupportWorkflow(
        ApiRetriever(), ApiGateway(), factory, checkpointer=InMemorySaver()
    )
    shared_api_session = factory()

    def override_db() -> Iterator[Session]:
        yield shared_api_session

    app = create_app(
        Settings(
            _env_file=None,
            app_env="testing",
            auth_jwt_secret=SECRET,
            auth_jwt_audience=AUDIENCE,
        )
    )
    app.dependency_overrides[get_support_db] = override_db
    app.dependency_overrides[get_workflow] = lambda: workflow
    client = TestClient(app)

    unauthorized = client.post("/api/v1/support/issues", json={"issue": "Activate SIM"})
    expired = client.post(
        "/api/v1/support/issues",
        headers={
            "Authorization": f"Bearer {_token(agent_id, 'support_agent', expired=True)}"
        },
        json={"issue": "Activate SIM"},
    )
    forged_role = client.post(
        "/api/v1/support/issues",
        headers={"Authorization": f"Bearer {_token(agent_id, 'admin')}"},
        json={"issue": "Activate SIM"},
    )
    unsupported_role = client.post(
        "/api/v1/support/issues",
        headers={
            "Authorization": f"Bearer {_token(unsupported_id, customer_role.name)}"
        },
        json={"issue": "Activate SIM"},
    )
    read_only = client.post(
        "/api/v1/support/issues",
        headers={
            "Authorization": f"Bearer {_token(agent_id, 'support_agent')}",
            "X-Actor-Id": str(admin_id),
            "X-Actor-Role": "admin",
        },
        json={"issue": "Activate SIM"},
    )
    proposed = client.post(
        "/api/v1/support/issues",
        headers={"Authorization": f"Bearer {_token(agent_id, 'support_agent')}"},
        json={
            "issue": "Resolve my ticket",
            "ticket_id": ticket_id,
            "propose_ticket_update": True,
        },
    )

    assert unauthorized.status_code == 401
    assert expired.status_code == 401
    assert forged_role.status_code == 403
    assert unsupported_role.status_code == 403
    assert read_only.status_code == 200
    assert read_only.json()["workflow_mode"] == "deterministic"
    assert read_only.json()["resolution"]["evidence"][0]["document_id"] == "api-guide"
    assert proposed.status_code == 200
    approval_id = proposed.json()["approval_id"]
    assert isinstance(approval_id, int), proposed.json()

    agent_denied = client.post(
        f"/api/v1/approvals/{approval_id}/decisions",
        headers={"Authorization": f"Bearer {_token(agent_id, 'support_agent')}"},
        json={"decision": "approve"},
    )
    approved = client.post(
        f"/api/v1/approvals/{approval_id}/decisions",
        headers={"Authorization": f"Bearer {_token(supervisor_id, 'supervisor')}"},
        json={"decision": "approve"},
    )
    viewed = client.get(
        f"/api/v1/approvals/{approval_id}",
        headers={"Authorization": f"Bearer {_token(admin_id, 'admin')}"},
    )
    malformed = client.post(
        "/api/v1/support/issues",
        headers={"Authorization": f"Bearer {_token(agent_id, 'support_agent')}"},
        json={"issue": "x", "unexpected": True},
    )

    assert agent_denied.status_code == 403, agent_denied.text
    assert approved.status_code == 200
    assert approved.json()["status"] == "completed"
    assert viewed.status_code == 200
    assert malformed.status_code == 422
    shared_api_session.close()
