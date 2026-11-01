"""MCP discovery, contract, and invocation tests."""

import asyncio

from mcp.client import Client
from qdrant_client import QdrantClient
from sqlalchemy import Connection, select
from sqlalchemy.orm import sessionmaker

from backend.app.db.seed import seed_fictional_data
from backend.app.knowledge.embeddings import DeterministicTelecomEmbeddings
from backend.app.knowledge.ingestion import ingest_knowledge
from backend.app.knowledge.retrieval import TelecomRetriever
from backend.app.mcp.customer_server import create_customer_server
from backend.app.mcp.knowledge_server import create_knowledge_server
from backend.app.mcp.ticket_server import create_ticket_server
from backend.app.models.customer import Customer
from backend.app.models.ticket import Ticket


def test_knowledge_mcp_discovery_and_invocation() -> None:
    async def scenario() -> None:
        qdrant = QdrantClient(location=":memory:")
        embeddings = DeterministicTelecomEmbeddings(128)
        ingest_knowledge(qdrant, collection_name="mcp_knowledge", embeddings=embeddings)
        server = create_knowledge_server(
            TelecomRetriever(qdrant, "mcp_knowledge", embeddings, minimum_score=0.03)
        )
        async with Client(server, raise_exceptions=True) as client:
            tools = await client.list_tools()
            assert {tool.name for tool in tools.tools} == {
                "search_knowledge_base",
                "get_policy",
                "get_source_details",
                "promote_knowledge",
            }
            result = await client.call_tool(
                "get_policy", {"policy_code": "ROAM-PASS-24"}
            )
            assert not result.is_error
            assert result.structured_content["found"] is True
            assert (
                result.structured_content["evidence"][0]["document_id"]
                == "policy-roaming-001"
            )

    asyncio.run(scenario())


def test_customer_and_ticket_mcp_contracts(test_db_connection: Connection) -> None:
    seed_fictional_data(test_db_connection)
    session_factory = sessionmaker(
        bind=test_db_connection,
        join_transaction_mode="create_savepoint",
    )
    with session_factory() as session:
        customer_id = session.scalar(
            select(Customer.id).where(Customer.customer_number == "FIC-CUST-001")
        )
        ticket_id = session.scalar(
            select(Ticket.id).where(Ticket.ticket_number == "FIC-TKT-001")
        )
    assert customer_id is not None and ticket_id is not None

    async def scenario() -> None:
        customer_server = create_customer_server(session_factory)
        ticket_server = create_ticket_server(session_factory)
        async with Client(customer_server, raise_exceptions=True) as client:
            tools = await client.list_tools()
            assert len(tools.tools) == 5
            result = await client.call_tool(
                "get_customer_profile", {"customer_id": customer_id}
            )
            assert result.structured_content["customer_number"] == "FIC-CUST-001"
            for tool_name in (
                "get_customer_plan",
                "check_roaming_status",
                "check_data_service_status",
                "get_active_services",
            ):
                result = await client.call_tool(tool_name, {"customer_id": customer_id})
                assert not result.is_error
        async with Client(ticket_server, raise_exceptions=True) as client:
            tools = await client.list_tools()
            assert {tool.name for tool in tools.tools} == {
                "get_ticket",
                "get_ticket_history",
                "draft_ticket_update",
                "update_ticket",
                "create_ticket",
            }
            denied = await client.call_tool(
                "update_ticket",
                {"ticket_id": ticket_id, "status": "resolved", "approval_id": 1},
            )
            assert denied.structured_content["executed"] is False
            assert denied.structured_content["code"] == "approval_required"
            ticket = await client.call_tool("get_ticket", {"ticket_id": ticket_id})
            history = await client.call_tool(
                "get_ticket_history", {"ticket_id": ticket_id}
            )
            draft = await client.call_tool(
                "draft_ticket_update",
                {"ticket_id": ticket_id, "note": "Fictional follow-up"},
            )
            create_denied = await client.call_tool(
                "create_ticket",
                {
                    "customer_id": customer_id,
                    "subject": "Fictional request",
                    "description": "Fictional controlled write probe",
                },
            )
            assert not ticket.is_error
            assert not history.is_error
            assert draft.structured_content["executable"] is False
            assert create_denied.structured_content["executed"] is False

    asyncio.run(scenario())


def test_mcp_invalid_arguments_return_protocol_error() -> None:
    async def scenario() -> None:
        qdrant = QdrantClient(location=":memory:")
        embeddings = DeterministicTelecomEmbeddings(128)
        ingest_knowledge(qdrant, collection_name="mcp_invalid", embeddings=embeddings)
        server = create_knowledge_server(
            TelecomRetriever(qdrant, "mcp_invalid", embeddings, minimum_score=0.03)
        )
        async with Client(server, raise_exceptions=False) as client:
            result = await client.call_tool("get_policy", {"wrong": "argument"})
            assert result.is_error

    asyncio.run(scenario())


def test_mcp_missing_customer_and_ticket_return_errors(
    test_db_connection: Connection,
) -> None:
    session_factory = sessionmaker(
        bind=test_db_connection,
        join_transaction_mode="create_savepoint",
    )

    async def scenario() -> None:
        async with Client(
            create_customer_server(session_factory), raise_exceptions=False
        ) as client:
            missing_customer = await client.call_tool(
                "get_customer_profile", {"customer_id": 999999999}
            )
            assert missing_customer.is_error
        async with Client(
            create_ticket_server(session_factory), raise_exceptions=False
        ) as client:
            missing_ticket = await client.call_tool(
                "get_ticket", {"ticket_id": 999999999}
            )
            assert missing_ticket.is_error

    asyncio.run(scenario())
