"""PostgreSQL approval scope, authorization, expiry, and replay tests."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import Connection, delete, select
from sqlalchemy.orm import sessionmaker

from backend.app.mcp.contracts import GatewayPrincipal
from backend.app.mcp.gateway import MCPGateway
from backend.app.mcp.ticket_server import create_ticket_server
from backend.app.models.audit_event import AuditEvent
from backend.app.models.customer import Customer
from backend.app.models.human_approval import HumanApproval
from backend.app.models.role import Role
from backend.app.models.subscription import Subscription  # noqa: F401
from backend.app.models.ticket import Ticket
from backend.app.models.user import User
from backend.app.schemas.support import ApprovalDecisionRequest, TicketDraft
from backend.app.services.approvals import ApprovalError, ApprovalService


def _session(test_db_connection: Connection):
    return sessionmaker(
        bind=test_db_connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )()


def _actor(session, role_name: str) -> User:
    suffix = uuid4().hex[:8]
    role = session.scalar(select(Role).where(Role.name == role_name))
    if role is None:
        role = Role(name=role_name, description="test")
        session.add(role)
        session.flush()
    actor = User(
        email=f"{suffix}@example.test", full_name="Test Actor", role_id=role.id
    )
    session.add(actor)
    session.flush()
    return actor


def test_approve_exact_scope_then_consume_blocks_replay(
    test_db_connection: Connection,
) -> None:
    session = _session(test_db_connection)
    actor = _actor(session, "supervisor")
    draft = TicketDraft(
        operation="update_ticket",
        payload={"ticket_id": 91, "status": "resolved", "priority": None},
    )
    approval = ApprovalService(session).request(
        thread_id=f"thread-{uuid4()}", draft=draft, ticket_id=None
    )
    ApprovalService(session).decide(
        approval.id, ApprovalDecisionRequest(decision="approve"), actor.id
    )
    verified = ApprovalService(session).verify(
        approval_id=approval.id,
        operation=draft.operation,
        payload=draft.payload,
        execution_request_id="execute-1",
    )
    ApprovalService(session).consume(verified, "execute-1")
    session.flush()
    with pytest.raises(ApprovalError, match="not executable"):
        ApprovalService(session).verify(
            approval_id=approval.id,
            operation=draft.operation,
            payload=draft.payload,
            execution_request_id="execute-2",
        )


def test_mismatch_rejection_and_expiry_fail_closed(
    test_db_connection: Connection,
) -> None:
    session = _session(test_db_connection)
    actor = _actor(session, "supervisor")
    draft = TicketDraft(
        operation="update_ticket",
        payload={"ticket_id": 92, "status": "resolved", "priority": None},
    )
    service = ApprovalService(session)
    approval = service.request(
        thread_id=f"thread-{uuid4()}", draft=draft, ticket_id=None
    )
    service.decide(approval.id, ApprovalDecisionRequest(decision="approve"), actor.id)
    with pytest.raises(ApprovalError, match="scope mismatch"):
        service.verify(
            approval_id=approval.id,
            operation="update_ticket",
            payload={**draft.payload, "status": "closed"},
            execution_request_id="execute-x",
        )
    approval.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    with pytest.raises(ApprovalError, match="expired"):
        service.verify(
            approval_id=approval.id,
            operation=draft.operation,
            payload=draft.payload,
            execution_request_id="execute-y",
        )


def test_support_agent_cannot_decide_approval(test_db_connection: Connection) -> None:
    session = _session(test_db_connection)
    actor = _actor(session, "support_agent")
    approval = ApprovalService(session).request(
        thread_id=f"thread-{uuid4()}",
        draft=TicketDraft(operation="update_ticket", payload={"ticket_id": 1}),
        ticket_id=None,
    )
    with pytest.raises(ApprovalError, match="supervisor"):
        ApprovalService(session).decide(
            approval.id, ApprovalDecisionRequest(decision="approve"), actor.id
        )


def test_gateway_and_ticket_tool_execute_exactly_one_approved_update(
    test_db_connection: Connection,
) -> None:
    factory = sessionmaker(
        bind=test_db_connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )
    with factory() as session:
        actor = _actor(session, "supervisor")
        suffix = uuid4().hex[:8]
        customer = Customer(
            customer_number=f"APP-{suffix}",
            full_name="Approval Test Customer",
            email=f"customer-{suffix}@example.test",
        )
        session.add(customer)
        session.flush()
        ticket = Ticket(
            ticket_number=f"APP-TKT-{suffix}",
            customer_id=customer.id,
            subject="Approval test",
            description="Fictional test ticket",
        )
        session.add(ticket)
        session.flush()
        payload = {
            "ticket_id": ticket.id,
            "status": "resolved",
            "priority": None,
        }
        approval = ApprovalService(session).request(
            thread_id=f"thread-{uuid4()}",
            draft=TicketDraft(operation="update_ticket", payload=payload),
            ticket_id=ticket.id,
        )
        ApprovalService(session).decide(
            approval.id, ApprovalDecisionRequest(decision="approve"), actor.id
        )
        session.commit()
        approval_id, actor_id, ticket_id = approval.id, actor.id, ticket.id

    async def scenario() -> None:
        gateway = MCPGateway(
            {"ticket": create_ticket_server(factory, controlled_writes_enabled=True)},
            approval_session_factory=factory,
        )
        principal = GatewayPrincipal(
            subject="supervisor", role="supervisor", actor_id=actor_id
        )
        first = await gateway.invoke(
            "ticket",
            "update_ticket",
            payload,
            principal,
            approval_id=approval_id,
            execution_request_id="approved-execution-1",
        )
        replay = await gateway.invoke(
            "ticket",
            "update_ticket",
            payload,
            principal,
            approval_id=approval_id,
            execution_request_id="approved-execution-2",
        )
        assert first.allowed and first.result["executed"] is True
        assert not replay.allowed

    asyncio.run(scenario())
    with factory() as session:
        assert session.get(Ticket, ticket_id).status == "resolved"


def test_edited_action_requires_new_approval(test_db_connection: Connection) -> None:
    session = _session(test_db_connection)
    actor = _actor(session, "supervisor")
    original = TicketDraft(
        operation="update_ticket",
        payload={"ticket_id": 12, "status": "resolved", "priority": None},
    )
    edited = TicketDraft(
        operation="update_ticket",
        payload={"ticket_id": 12, "status": "closed", "priority": "high"},
    )
    service = ApprovalService(session)
    old = service.request(thread_id=f"thread-{uuid4()}", draft=original, ticket_id=None)
    service.decide(
        old.id, ApprovalDecisionRequest(decision="edit", edited_action=edited), actor.id
    )
    replacement = service.request(thread_id=old.thread_id, draft=edited, ticket_id=None)
    with pytest.raises(ApprovalError, match="not executable"):
        service.verify(
            approval_id=old.id,
            operation=edited.operation,
            payload=edited.payload,
            execution_request_id="old-scope",
        )
    with pytest.raises(ApprovalError, match="not executable"):
        service.verify(
            approval_id=replacement.id,
            operation=edited.operation,
            payload=edited.payload,
            execution_request_id="before-approval",
        )
    service.decide(
        replacement.id, ApprovalDecisionRequest(decision="approve"), actor.id
    )
    assert (
        service.verify(
            approval_id=replacement.id,
            operation=edited.operation,
            payload=edited.payload,
            execution_request_id="new-scope",
        ).id
        == replacement.id
    )


def test_approved_ticket_creation_executes_once(test_db_connection: Connection) -> None:
    factory = sessionmaker(
        bind=test_db_connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )
    with factory() as session:
        actor = _actor(session, "supervisor")
        suffix = uuid4().hex[:8]
        customer = Customer(customer_number=f"CRT-{suffix}", full_name="Creation Test")
        session.add(customer)
        session.flush()
        payload = {
            "customer_id": customer.id,
            "subject": "Created safely",
            "description": "Fictional approved creation",
            "priority": "medium",
        }
        approval = ApprovalService(session).request(
            thread_id=f"thread-{uuid4()}",
            draft=TicketDraft(operation="create_ticket", payload=payload),
            ticket_id=None,
        )
        ApprovalService(session).decide(
            approval.id, ApprovalDecisionRequest(decision="approve"), actor.id
        )
        session.commit()
        approval_id, actor_id = approval.id, actor.id

    async def scenario() -> tuple[int, bool]:
        gateway = MCPGateway(
            {"ticket": create_ticket_server(factory, controlled_writes_enabled=True)},
            approval_session_factory=factory,
        )
        response = await gateway.invoke(
            "ticket",
            "create_ticket",
            payload,
            GatewayPrincipal(
                subject="supervisor", role="supervisor", actor_id=actor_id
            ),
            approval_id=approval_id,
            execution_request_id=f"create-{suffix}",
        )
        replay = await gateway.invoke(
            "ticket",
            "create_ticket",
            payload,
            GatewayPrincipal(
                subject="supervisor", role="supervisor", actor_id=actor_id
            ),
            approval_id=approval_id,
            execution_request_id=f"create-{suffix}",
        )
        assert response.allowed and response.result["executed"] is True
        return response.result["ticket_id"], replay.allowed

    ticket_id, replay_allowed = asyncio.run(scenario())
    assert replay_allowed is False
    with factory() as session:
        assert session.get(Ticket, ticket_id) is not None


def test_ticket_transaction_rolls_back_when_consumption_fails(
    test_db_connection: Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    factory = sessionmaker(
        bind=test_db_connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )
    with factory() as session:
        actor = _actor(session, "supervisor")
        suffix = uuid4().hex[:8]
        customer = Customer(customer_number=f"RBK-{suffix}", full_name="Rollback Test")
        session.add(customer)
        session.flush()
        ticket = Ticket(
            ticket_number=f"RBK-TKT-{suffix}",
            customer_id=customer.id,
            subject="Rollback",
            description="Fictional rollback",
        )
        session.add(ticket)
        session.flush()
        payload = {"ticket_id": ticket.id, "status": "resolved", "priority": None}
        approval = ApprovalService(session).request(
            thread_id=f"thread-{uuid4()}",
            draft=TicketDraft(operation="update_ticket", payload=payload),
            ticket_id=ticket.id,
        )
        ApprovalService(session).decide(
            approval.id, ApprovalDecisionRequest(decision="approve"), actor.id
        )
        session.commit()
        approval_id, actor_id, ticket_id = approval.id, actor.id, ticket.id

    def fail_consume(*args: object, **kwargs: object) -> None:
        raise RuntimeError("simulated transactional failure")

    monkeypatch.setattr(ApprovalService, "consume", fail_consume)

    async def scenario() -> None:
        gateway = MCPGateway(
            {"ticket": create_ticket_server(factory, controlled_writes_enabled=True)},
            approval_session_factory=factory,
        )
        response = await gateway.invoke(
            "ticket",
            "update_ticket",
            payload,
            GatewayPrincipal(
                subject="supervisor", role="supervisor", actor_id=actor_id
            ),
            approval_id=approval_id,
            execution_request_id="rollback-execution",
        )
        assert not response.allowed and response.error.code == "tool_error"

    asyncio.run(scenario())
    with factory() as session:
        assert session.get(Ticket, ticket_id).status == "open"
        assert session.get(HumanApproval, approval_id).consumed is False


def test_concurrent_decisions_allow_one_transition(test_db_engine) -> None:
    factory = sessionmaker(bind=test_db_engine, expire_on_commit=False)
    with factory() as session, session.begin():
        actor = _actor(session, "supervisor")
        approval = ApprovalService(session).request(
            thread_id=f"concurrent-{uuid4()}",
            draft=TicketDraft(operation="update_ticket", payload={"ticket_id": 999}),
            ticket_id=None,
        )
        actor_id, approval_id = actor.id, approval.id

    def decide(decision: str) -> str:
        with factory() as session:
            try:
                ApprovalService(session).decide(
                    approval_id, ApprovalDecisionRequest(decision=decision), actor_id
                )
                session.commit()
                return "transitioned"
            except ApprovalError:
                session.rollback()
                return "denied"

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(decide, ["approve", "reject"]))
        assert sorted(results) == ["denied", "transitioned"]
    finally:
        with factory() as session, session.begin():
            session.execute(
                delete(AuditEvent).where(
                    AuditEvent.resource_type == "human_approval",
                    AuditEvent.resource_id == str(approval_id),
                )
            )
            session.execute(
                delete(HumanApproval).where(HumanApproval.id == approval_id)
            )
            session.execute(delete(User).where(User.id == actor_id))
