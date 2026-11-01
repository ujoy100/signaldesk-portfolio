"""Real PostgreSQL LangGraph checkpoint restart and recovery tests."""

import asyncio
from uuid import uuid4

import pytest
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.types import Command
from sqlalchemy import delete
from sqlalchemy.orm import sessionmaker

from backend.app.db.urls import postgres_checkpoint_url
from backend.app.knowledge.models import Evidence, RetrievalResponse
from backend.app.mcp.contracts import GatewayResponse
from backend.app.models.audit_event import AuditEvent
from backend.app.models.customer import Customer
from backend.app.models.human_approval import HumanApproval
from backend.app.models.subscription import Subscription  # noqa: F401
from backend.app.models.ticket import Ticket
from backend.app.workflow.graph import SupportWorkflow
from backend.scripts.setup_checkpoints import setup_checkpoint_schema


class CheckpointRetriever:
    def retrieve(self, query: str, **kwargs: object) -> RetrievalResponse:
        return RetrievalResponse(
            answered=True,
            strategy="hybrid_reranked",
            evidence=[
                Evidence(
                    chunk_id="restart-evidence",
                    document_id="restart-doc",
                    source="fictional",
                    title="Restart evidence",
                    section="test",
                    page=1,
                    version="1.0",
                    service="mobile",
                    category="support",
                    content="Fictional evidence for checkpoint restart testing.",
                    score=0.8,
                    retrieval_signals=["test"],
                )
            ],
        )


class CountingGateway:
    def __init__(self) -> None:
        self.executions = 0

    async def invoke(
        self,
        namespace: str,
        tool: str,
        arguments: dict,
        *args: object,
        **kwargs: object,
    ) -> GatewayResponse:
        if tool == "update_ticket":
            self.executions += 1
            return GatewayResponse(
                request_id=f"restart-write-{self.executions}",
                namespace=namespace,
                tool=tool,
                allowed=True,
                result={"executed": True, "code": "executed", "message": "test"},
            )
        if tool != "get_ticket_history":
            raise AssertionError("unexpected tool")
        return GatewayResponse(
            request_id="restart-read",
            namespace=namespace,
            tool=tool,
            allowed=True,
            result={"ticket_id": arguments["ticket_id"], "events": []},
        )


@pytest.fixture
def checkpoint_url(test_db_engine) -> str:
    """Provision the official schema for this isolated integration boundary."""

    setup_checkpoint_schema(test_db_engine.url)
    return postgres_checkpoint_url(test_db_engine.url)


def test_postgres_checkpoint_survives_graph_reconstruction(
    test_db_engine, checkpoint_url: str
) -> None:
    thread_id = f"restart-{uuid4()}"
    suffix = uuid4().hex[:10]
    factory = sessionmaker(bind=test_db_engine, expire_on_commit=False)
    with factory() as session, session.begin():
        customer = Customer(
            customer_number=f"RST-{suffix}",
            full_name="Restart Test",
            email=f"restart-{suffix}@example.test",
        )
        session.add(customer)
        session.flush()
        ticket = Ticket(
            ticket_number=f"RST-TKT-{suffix}",
            customer_id=customer.id,
            subject="Restart test",
            description="Fictional restart test ticket",
        )
        session.add(ticket)
        session.flush()
        ticket_id = ticket.id

    config = {"configurable": {"thread_id": thread_id}}
    gateway = CountingGateway()
    try:

        async def scenario() -> tuple[int, dict]:
            async with AsyncPostgresSaver.from_conn_string(
                checkpoint_url
            ) as first_saver:
                first = SupportWorkflow(
                    CheckpointRetriever(),
                    gateway,
                    factory,
                    checkpointer=first_saver,
                )
                initial = await first.graph.ainvoke(
                    {
                        "issue": "Resolve the test ticket",
                        "thread_id": thread_id,
                        "customer_id": None,
                        "ticket_id": ticket_id,
                        "propose_ticket_update": True,
                        "principal": {
                            "subject": "agent",
                            "role": "support_agent",
                            "actor_id": 1,
                        },
                    },
                    config,
                )
                approval_id = initial["approval_id"]
                assert initial["__interrupt__"]

            async with AsyncPostgresSaver.from_conn_string(
                checkpoint_url
            ) as second_saver:
                reconstructed = SupportWorkflow(
                    CheckpointRetriever(),
                    gateway,
                    factory,
                    checkpointer=second_saver,
                )
                saved = await reconstructed.graph.aget_state(config)
                assert saved.values["approval_id"] == approval_id
                assert saved.values["thread_id"] == thread_id
                resumed = await reconstructed.graph.ainvoke(
                    Command(
                        resume={"decision": "approve"},
                        update={
                            "principal": {
                                "subject": "supervisor",
                                "role": "supervisor",
                                "actor_id": 2,
                            }
                        },
                    ),
                    config,
                )
                assert resumed["status"] == "completed"
                assert resumed["approval_decision"] == "approve"
                assert gateway.executions == 1
                repeated = await reconstructed.graph.ainvoke(
                    Command(resume={"decision": "approve"}), config
                )
                assert repeated["status"] == "completed"
                assert gateway.executions == 1
                await second_saver.adelete_thread(thread_id)

            async with AsyncPostgresSaver.from_conn_string(
                checkpoint_url
            ) as third_saver:
                missing_graph = SupportWorkflow(
                    CheckpointRetriever(),
                    gateway,
                    factory,
                    checkpointer=third_saver,
                ).graph
                missing = await missing_graph.aget_state(
                    {"configurable": {"thread_id": f"missing-{uuid4()}"}}
                )
                assert not missing.values
            return approval_id, resumed

        asyncio.run(scenario())
    finally:
        with factory() as session, session.begin():
            session.execute(
                delete(AuditEvent).where(AuditEvent.details.contains(thread_id))
            )
            session.execute(
                delete(HumanApproval).where(HumanApproval.thread_id == thread_id)
            )
            session.execute(delete(Ticket).where(Ticket.id == ticket_id))
            session.execute(
                delete(Customer).where(Customer.customer_number == f"RST-{suffix}")
            )
