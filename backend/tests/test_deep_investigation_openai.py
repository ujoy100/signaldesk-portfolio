"""Opt-in genuine OpenAI/Deep Agents Phase 10 acceptance test."""

import asyncio
import os
from uuid import uuid4

import pytest
from langgraph.checkpoint.memory import InMemorySaver
from qdrant_client import QdrantClient
from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.config import Settings
from backend.app.db.seed import seed_fictional_data
from backend.app.knowledge.embeddings import DeterministicTelecomEmbeddings
from backend.app.knowledge.ingestion import ingest_knowledge
from backend.app.knowledge.retrieval import TelecomRetriever
from backend.app.mcp.customer_server import create_customer_server
from backend.app.mcp.gateway import CONTROLLED_WRITES, MCPGateway
from backend.app.mcp.knowledge_server import create_knowledge_server
from backend.app.mcp.ticket_server import create_ticket_server
from backend.app.models.customer import Customer
from backend.app.models.role import Role
from backend.app.models.ticket import Ticket
from backend.app.models.user import User
from backend.app.workflow.graph import SupportWorkflow
from backend.app.workflow.investigation import DeepAgentInvestigator

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_PHASE10_MODEL_TEST") != "yes",
    reason="opt-in real-model acceptance; offline CI remains deterministic",
)


def test_real_openai_repeated_roaming_investigation(
    test_db_engine: Engine,
) -> None:
    settings = Settings()
    assert settings.openai_api_key is not None, "OPENAI_API_KEY must be configured"
    assert settings.deep_agent_model == "openai:gpt-4.1-mini"

    with test_db_engine.begin() as connection:
        seed_fictional_data(connection)
    factory = sessionmaker(
        bind=test_db_engine,
        expire_on_commit=False,
    )
    with factory() as session:
        role = session.scalar(select(Role).where(Role.name == "support_agent"))
        if role is None:
            role = Role(name="support_agent", description="Support Agent")
            session.add(role)
            session.flush()
        actor = session.scalar(
            select(User).where(User.email == "phase10-model@example.test")
        )
        if actor is None:
            actor = User(
                email="phase10-model@example.test",
                full_name="Fictional Phase 10 Agent",
                role_id=role.id,
                is_active=True,
            )
            session.add(actor)
        else:
            actor.role_id = role.id
            actor.is_active = True
        session.commit()
        actor_id = actor.id

        customer_id = session.scalar(
            select(Customer.id).where(Customer.customer_number == "FIC-CUST-001")
        )
        ticket_id = session.scalar(
            select(Ticket.id).where(Ticket.ticket_number == "FIC-TKT-001")
        )
    assert customer_id is not None and ticket_id is not None

    qdrant = QdrantClient(location=":memory:")
    embeddings = DeterministicTelecomEmbeddings(128)
    collection = f"phase10_openai_{uuid4().hex}"
    ingest_knowledge(qdrant, collection_name=collection, embeddings=embeddings)
    retriever = TelecomRetriever(qdrant, collection, embeddings, minimum_score=0.03)
    audit: list[dict] = []

    async def audit_writer(event: dict) -> None:
        audit.append(event)

    gateway = MCPGateway(
        {
            "knowledge": create_knowledge_server(retriever),
            "customer": create_customer_server(factory),
            "ticket": create_ticket_server(factory),
        },
        audit_writer=audit_writer,
        identity_session_factory=factory,
        timeout_seconds=5,
    )
    investigator = DeepAgentInvestigator(
        gateway,
        model=settings.deep_agent_model,
        openai_api_key=settings.openai_api_key,
        max_steps=8,
        max_tool_calls=6,
        timeout_seconds=60,
    )
    workflow = SupportWorkflow(
        retriever,
        gateway,
        factory,
        checkpointer=InMemorySaver(),
        investigator=investigator,
    )
    principal = {
        "subject": f"user:{actor_id}",
        "role": "support_agent",
        "actor_id": actor_id,
    }

    async def scenario() -> None:
        complex_result = await workflow.graph.ainvoke(
            {
                "issue": (
                    "Repeated roaming activation failures happened again. Investigate "
                    "the fictional customer's plan eligibility, policy ROAM-PASS-24, "
                    "and historical ticket evidence before recommending next steps."
                ),
                "thread_id": "phase10-real-roaming-001",
                "customer_id": customer_id,
                "ticket_id": ticket_id,
                "propose_ticket_update": False,
                "principal": principal,
            },
            {"configurable": {"thread_id": "phase10-real-roaming-001"}},
        )
        assert complex_result["complexity"] == "investigation"
        investigation = complex_result["investigation"]
        assert investigation["tool_calls_performed"]
        assert investigation["supporting_evidence"]
        evidence_ids = {
            item["source_id"] for item in investigation["supporting_evidence"]
        }
        assert investigation["citations"]
        assert set(investigation["citations"]) <= evidence_ids
        assert len(investigation["tool_calls_performed"]) <= 6
        assert complex_result["resolution"]["action_required"] is False
        assert complex_result["status"] == "completed"

        called = {
            f"{event['namespace']}.{event['tool']}"
            for event in audit
            if event["allowed"]
        }
        assert "customer.get_customer_plan" in called
        assert "ticket.get_ticket_history" in called
        assert called.isdisjoint(CONTROLLED_WRITES)

        audit_count = len(audit)
        simple_result = await workflow.graph.ainvoke(
            {
                "issue": "How do I activate my fictional SIM?",
                "thread_id": "phase10-real-simple-001",
                "customer_id": None,
                "ticket_id": None,
                "propose_ticket_update": False,
                "principal": principal,
            },
            {"configurable": {"thread_id": "phase10-real-simple-001"}},
        )
        assert simple_result["complexity"] == "simple"
        assert len(audit) == audit_count

    asyncio.run(scenario())
