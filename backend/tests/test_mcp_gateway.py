"""MCP Gateway routing and authorization tests."""

import asyncio
from uuid import uuid4

from qdrant_client import QdrantClient
from sqlalchemy import Connection, func, select
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import Settings
from backend.app.knowledge.embeddings import DeterministicTelecomEmbeddings
from backend.app.knowledge.ingestion import ingest_knowledge
from backend.app.knowledge.retrieval import TelecomRetriever
from backend.app.mcp.contracts import GatewayPrincipal, KnowledgePromotionOutput
from backend.app.mcp.gateway import MCPGateway, create_database_audit_writer
from backend.app.mcp.knowledge_server import create_knowledge_server
from backend.app.models.audit_event import AuditEvent
from backend.app.models.role import Role
from backend.app.models.subscription import Subscription  # noqa: F401
from backend.app.models.ticket import Ticket  # noqa: F401
from backend.app.models.user import User
from backend.app.schemas.support import ApprovalDecisionRequest
from backend.app.services.approvals import ApprovalService
from backend.tests.test_auth import issue_token


def _gateway(audit_events: list[dict]) -> MCPGateway:
    qdrant = QdrantClient(location=":memory:")
    embeddings = DeterministicTelecomEmbeddings(128)
    ingest_knowledge(qdrant, collection_name="gateway", embeddings=embeddings)

    async def audit(event: dict) -> None:
        audit_events.append(event)

    return MCPGateway(
        {
            "knowledge": create_knowledge_server(
                TelecomRetriever(qdrant, "gateway", embeddings, minimum_score=0.03)
            )
        },
        audit_writer=audit,
    )


def test_gateway_discovers_and_routes_namespaced_mcp_call() -> None:
    async def scenario() -> None:
        audit: list[dict] = []
        gateway = _gateway(audit)
        principal = GatewayPrincipal(subject="agent-1", role="support_agent")

        discovery = await gateway.discover(principal)
        response = await gateway.invoke(
            "knowledge",
            "get_policy",
            {"policy_code": "BILL-DISPUTE-30"},
            principal,
        )

        assert "get_policy" in discovery["knowledge"]
        assert response.allowed
        assert response.result["found"] is True
        assert audit[-1]["request_id"] == response.request_id

    asyncio.run(scenario())


def test_gateway_denies_role_and_approval_bypass() -> None:
    async def scenario() -> None:
        audit: list[dict] = []
        gateway = _gateway(audit)
        customer = GatewayPrincipal(subject="customer-1", role="customer")
        agent = GatewayPrincipal(subject="agent-1", role="support_agent")

        role_denied = await gateway.invoke(
            "customer", "get_customer_profile", {"customer_id": 1}, customer
        )
        write_denied = await gateway.invoke(
            "ticket",
            "update_ticket",
            {"ticket_id": 1, "status": "resolved"},
            agent,
            approval_id=1,
            execution_request_id="attempt-1",
        )

        assert not role_denied.allowed
        assert role_denied.error.code == "access_denied"
        assert not write_denied.allowed
        assert "approval" in write_denied.error.message
        assert len(audit) == 2

    asyncio.run(scenario())


def test_gateway_handles_unavailable_unsupported_and_invalid_calls() -> None:
    async def scenario() -> None:
        gateway = _gateway([])
        principal = GatewayPrincipal(subject="agent-1", role="support_agent")

        unavailable = await gateway.invoke(
            "customer", "get_customer_profile", {"customer_id": 1}, principal
        )
        unsupported = await gateway.invoke("knowledge", "missing_tool", {}, principal)
        invalid = await gateway.invoke(
            "knowledge", "get_policy", {"wrong": "value"}, principal
        )

        assert unavailable.error.code == "service_unavailable"
        assert unsupported.error.code == "unsupported_tool"
        assert invalid.error.code == "tool_error"

    asyncio.run(scenario())


def test_gateway_authenticates_before_routing() -> None:
    async def scenario() -> None:
        gateway = _gateway([])
        settings = Settings(
            _env_file=None,
            auth_jwt_secret="test-only-secret-with-sufficient-entropy",
            auth_jwt_audience="telecom-tests",
        )

        response = await gateway.invoke_authenticated(
            issue_token(),
            settings,
            "knowledge",
            "get_policy",
            {"policy_code": "ROAM-PASS-24"},
        )

        assert response.allowed
        assert response.result["found"] is True

    asyncio.run(scenario())


def test_gateway_persists_audit_decision(test_db_connection: Connection) -> None:
    async def scenario() -> None:
        session_factory = sessionmaker(
            bind=test_db_connection,
            join_transaction_mode="create_savepoint",
        )
        base = _gateway([])
        gateway = MCPGateway(
            base.servers,
            audit_writer=create_database_audit_writer(session_factory),
        )
        principal = GatewayPrincipal(subject="service-agent", role="support_agent")

        response = await gateway.invoke(
            "knowledge",
            "get_policy",
            {"policy_code": "ROAM-PASS-24"},
            principal,
        )

        assert response.allowed
        with session_factory() as session:
            count = session.scalar(
                select(func.count())
                .select_from(AuditEvent)
                .where(
                    AuditEvent.action == "mcp_gateway_call",
                    AuditEvent.details.contains(response.request_id),
                )
            )
        assert count == 1

    asyncio.run(scenario())


def test_gateway_independently_rejects_forged_or_inactive_database_identity(
    test_db_connection: Connection,
) -> None:
    session_factory = sessionmaker(
        bind=test_db_connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )
    with session_factory() as session:
        role = session.scalar(select(Role).where(Role.name == "support_agent"))
        if role is None:
            role = Role(name="support_agent")
            session.add(role)
            session.flush()
        actor = User(
            email=f"gateway-identity-{uuid4()}@example.test",
            full_name="Gateway Identity",
            role_id=role.id,
            is_active=True,
        )
        inactive = User(
            email=f"gateway-inactive-{uuid4()}@example.test",
            full_name="Inactive Identity",
            role_id=role.id,
            is_active=False,
        )
        session.add_all([actor, inactive])
        session.commit()
        actor_id, inactive_id = actor.id, inactive.id

    async def scenario() -> None:
        base = _gateway([])
        gateway = MCPGateway(base.servers, identity_session_factory=session_factory)
        valid = await gateway.invoke(
            "knowledge",
            "get_policy",
            {"policy_code": "ROAM-PASS-24"},
            GatewayPrincipal(subject="valid", role="support_agent", actor_id=actor_id),
        )
        forged = await gateway.invoke(
            "knowledge",
            "get_policy",
            {"policy_code": "ROAM-PASS-24"},
            GatewayPrincipal(subject="forged", role="admin", actor_id=actor_id),
        )
        inactive = await gateway.invoke(
            "knowledge",
            "get_policy",
            {"policy_code": "ROAM-PASS-24"},
            GatewayPrincipal(
                subject="inactive", role="support_agent", actor_id=inactive_id
            ),
        )
        assert valid.allowed
        assert not forged.allowed and "mismatch" in forged.error.message
        assert not inactive.allowed and "mismatch" in inactive.error.message

    asyncio.run(scenario())


def test_gateway_requires_exact_approval_for_knowledge_promotion(
    test_db_connection: Connection,
) -> None:
    session_factory = sessionmaker(
        bind=test_db_connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )
    scope = {
        "version_id": 41,
        "document_id": "fictional-document-id",
        "version": "2.0",
        "checksum": "a" * 64,
    }
    with session_factory() as session:
        role = session.scalar(select(Role).where(Role.name == "supervisor"))
        if role is None:
            role = Role(name="supervisor")
            session.add(role)
            session.flush()
        actor = User(
            email=f"promotion-{uuid4()}@example.test",
            full_name="Promotion Supervisor",
            role_id=role.id,
        )
        session.add(actor)
        session.flush()
        approval = ApprovalService(session).request_action(
            thread_id=f"promotion-{uuid4()}",
            operation="promote_knowledge",
            payload=scope,
        )
        ApprovalService(session).decide(
            approval.id, ApprovalDecisionRequest(decision="approve"), actor.id
        )
        session.commit()
        approval_id, actor_id = approval.id, actor.id

    qdrant = QdrantClient(location=":memory:")
    embeddings = DeterministicTelecomEmbeddings(128)
    ingest_knowledge(qdrant, collection_name="promotion_gateway", embeddings=embeddings)

    def promote_handler(**arguments: object) -> KnowledgePromotionOutput:
        return KnowledgePromotionOutput(
            executed=True,
            version_id=int(arguments["version_id"]),
            status="active",
            promotion_state="published",
        )

    server = create_knowledge_server(
        TelecomRetriever(qdrant, "promotion_gateway", embeddings),
        promotion_handler=promote_handler,
    )

    async def scenario() -> None:
        gateway = MCPGateway(
            {"knowledge": server}, approval_session_factory=session_factory
        )
        principal = GatewayPrincipal(
            subject="supervisor", role="supervisor", actor_id=actor_id
        )
        allowed = await gateway.invoke(
            "knowledge",
            "promote_knowledge",
            scope,
            principal,
            approval_id=approval_id,
            execution_request_id="knowledge-execution",
        )
        mismatched = await gateway.invoke(
            "knowledge",
            "promote_knowledge",
            {**scope, "checksum": "b" * 64},
            principal,
            approval_id=approval_id,
            execution_request_id="knowledge-execution",
        )
        assert not mismatched.allowed
        assert allowed.allowed and allowed.result["promotion_state"] == "published"

    asyncio.run(scenario())
