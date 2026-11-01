"""Knowledge MCP server."""

from collections.abc import Callable

from mcp.server import MCPServer
from qdrant_client import models

from backend.app.knowledge.models import RetrievalFilters
from backend.app.knowledge.retrieval import TelecomRetriever
from backend.app.mcp.contracts import (
    KnowledgePromotionOutput,
    KnowledgeSearchOutput,
    PolicyOutput,
    SourceDetailsOutput,
)


def create_knowledge_server(
    retriever: TelecomRetriever,
    *,
    promotion_handler: Callable[..., KnowledgePromotionOutput] | None = None,
) -> MCPServer:
    server = MCPServer("telecom-knowledge", version="1.0.0")

    @server.tool(structured_output=True)
    def search_knowledge_base(
        query: str,
        service: str | None = None,
        category: str | None = None,
        access_roles: list[str] | None = None,
        limit: int = 4,
    ) -> KnowledgeSearchOutput:
        """Search active telecom knowledge with metadata and access filters."""

        response = retriever.retrieve(
            query,
            filters=RetrievalFilters(
                service=service,
                category=category,
                access_roles=access_roles or ["public"],
            ),
            limit=min(max(limit, 1), 10),
        )
        return KnowledgeSearchOutput(
            answered=response.answered,
            evidence=[item.model_dump() for item in response.evidence],
            reason=response.reason,
        )

    @server.tool(structured_output=True)
    def get_policy(
        policy_code: str, access_roles: list[str] | None = None
    ) -> PolicyOutput:
        """Retrieve active evidence for an exact fictional policy code."""

        response = retriever.retrieve(
            policy_code,
            strategy="hybrid_reranked",
            filters=RetrievalFilters(access_roles=access_roles or ["public"]),
            limit=3,
        )
        return PolicyOutput(
            found=response.answered,
            policy_code=policy_code,
            evidence=[item.model_dump() for item in response.evidence],
        )

    @server.tool(structured_output=True)
    def get_source_details(document_id: str) -> SourceDetailsOutput:
        """Return lineage metadata for one active source document."""

        records, _ = retriever.client.scroll(
            collection_name=retriever.collection_name,
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="document_id", match=models.MatchValue(value=document_id)
                    ),
                    models.FieldCondition(
                        key="active", match=models.MatchValue(value=True)
                    ),
                ]
            ),
            limit=1,
            with_payload=True,
        )
        if not records:
            return SourceDetailsOutput(found=False, document_id=document_id)
        payload = records[0].payload or {}
        return SourceDetailsOutput(
            found=True,
            document_id=document_id,
            source=payload.get("source"),
            title=payload.get("title"),
            version=payload.get("version"),
            active=payload.get("active"),
        )

    @server.tool(structured_output=True)
    def promote_knowledge(
        version_id: int,
        document_id: str,
        version: str,
        checksum: str,
        approval_id: int | None = None,
        execution_request_id: str | None = None,
    ) -> KnowledgePromotionOutput:
        """Execute an exact approved authoritative promotion."""

        if promotion_handler is None or approval_id is None or not execution_request_id:
            raise PermissionError("verified promotion handler and approval required")
        return promotion_handler(
            version_id=version_id,
            document_id=document_id,
            version=version,
            checksum=checksum,
            approval_id=approval_id,
            execution_request_id=execution_request_id,
        )

    return server
