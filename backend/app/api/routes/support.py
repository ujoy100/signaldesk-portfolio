"""Authenticated support workflow and human-approval endpoints."""

import json
from collections.abc import AsyncGenerator, Generator
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, status
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.types import Command
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.api.routes.knowledge_admin import get_actor
from backend.app.db.urls import postgres_checkpoint_url
from backend.app.knowledge.client import create_qdrant_client
from backend.app.knowledge.embeddings import DeterministicTelecomEmbeddings
from backend.app.knowledge.retrieval import TelecomRetriever
from backend.app.mcp.contracts import GatewayPrincipal
from backend.app.mcp.customer_server import create_customer_server
from backend.app.mcp.gateway import MCPGateway, create_database_audit_writer
from backend.app.mcp.knowledge_server import create_knowledge_server
from backend.app.mcp.ticket_server import create_ticket_server
from backend.app.models.human_approval import HumanApproval
from backend.app.models.role import Role
from backend.app.models.user import User
from backend.app.observability import telemetry
from backend.app.schemas.support import (
    ApprovalDecisionRequest,
    ApprovalResponse,
    SupportIssueRequest,
    SupportResolution,
    WorkflowResponse,
)
from backend.app.services.approvals import ApprovalError, ApprovalService
from backend.app.workflow.graph import SupportWorkflow
from backend.app.workflow.investigation import DeepAgentInvestigator

router = APIRouter(prefix="/api/v1", tags=["support-workflow"])


async def get_workflow(request: Request) -> AsyncGenerator[SupportWorkflow]:
    settings = request.app.state.settings
    workflow_engine = create_engine(settings.database_url, pool_pre_ping=True)
    factory = sessionmaker(bind=workflow_engine, expire_on_commit=False)
    qdrant = create_qdrant_client(settings)
    embeddings = DeterministicTelecomEmbeddings(settings.embedding_dimensions)
    retriever = TelecomRetriever(
        qdrant,
        settings.qdrant_collection,
        embeddings,
        minimum_score=settings.retrieval_min_score,
        telemetry_recorder=telemetry,
    )
    gateway = MCPGateway(
        {
            "knowledge": create_knowledge_server(retriever),
            "customer": create_customer_server(factory),
            "ticket": create_ticket_server(factory, controlled_writes_enabled=True),
        },
        audit_writer=create_database_audit_writer(factory),
        approval_session_factory=factory,
        identity_session_factory=factory,
        telemetry_recorder=telemetry,
    )
    investigator = (
        DeepAgentInvestigator(
            gateway,
            model=settings.deep_agent_model,
            openai_api_key=settings.openai_api_key,
            max_steps=settings.deep_agent_max_steps,
            max_tool_calls=settings.deep_agent_max_tool_calls,
            timeout_seconds=settings.deep_agent_timeout_seconds,
            telemetry_recorder=telemetry,
        )
        if settings.deep_agent_model
        else None
    )
    checkpoint_url = postgres_checkpoint_url(settings.database_url)
    async with AsyncPostgresSaver.from_conn_string(checkpoint_url) as saver:
        try:
            yield SupportWorkflow(
                retriever,
                gateway,
                factory,
                checkpointer=saver,
                investigator=investigator,
                telemetry_recorder=telemetry,
            )
        finally:
            workflow_engine.dispose()


def get_support_db(request: Request) -> Generator[Session]:
    """Bind support routes to the application settings, not import-time globals."""

    support_engine = create_engine(
        request.app.state.settings.database_url, pool_pre_ping=True
    )
    try:
        with Session(support_engine) as session:
            yield session
    finally:
        support_engine.dispose()


def get_verified_actor(
    actor: Annotated[tuple[int, str], Depends(get_actor)],
    session: Annotated[Session, Depends(get_support_db)],
) -> tuple[int, str]:
    """Bind verified JWT claims to one active database user and role."""

    database_role = session.scalar(
        select(Role.name)
        .join(User, User.role_id == Role.id)
        .where(User.id == actor[0], User.is_active.is_(True))
    )
    if database_role is None or database_role != actor[1]:
        raise HTTPException(
            status_code=403, detail="Authenticated identity is not authorized"
        )
    if database_role not in {"support_agent", "supervisor", "admin"}:
        raise HTTPException(status_code=403, detail="Unsupported support role")
    return actor


def _response(thread_id: str, result: dict) -> WorkflowResponse:
    interrupted = result.get("__interrupt__")
    return WorkflowResponse(
        thread_id=thread_id,
        status="approval_pending" if interrupted else result.get("status", "completed"),
        resolution=SupportResolution.model_validate(result["resolution"])
        if result.get("resolution")
        else None,
        approval_id=result.get("approval_id"),
        error=";".join(result.get("errors", [])) or None,
        workflow_mode=(
            "deep_agent"
            if result.get("complexity") == "investigation"
            else "deterministic"
        ),
    )


@router.post("/support/issues", response_model=WorkflowResponse)
async def submit_issue(
    payload: SupportIssueRequest,
    actor: Annotated[tuple[int, str], Depends(get_verified_actor)],
    workflow: Annotated[SupportWorkflow, Depends(get_workflow)],
) -> WorkflowResponse:
    thread_id = payload.thread_id or str(uuid4())
    state = {
        **payload.model_dump(exclude={"thread_id"}),
        "thread_id": thread_id,
        "principal": GatewayPrincipal(
            subject=f"user:{actor[0]}", role=actor[1], actor_id=actor[0]
        ).model_dump(),
    }
    result = await workflow.graph.ainvoke(
        state, {"configurable": {"thread_id": thread_id}}
    )
    return _response(thread_id, result)


@router.get("/approvals/{approval_id}", response_model=ApprovalResponse)
def view_approval(
    approval_id: int,
    actor: Annotated[tuple[int, str], Depends(get_verified_actor)],
    session: Annotated[Session, Depends(get_support_db)],
) -> ApprovalResponse:
    if actor[1] not in {"supervisor", "admin"}:
        raise HTTPException(status_code=403, detail="Supervisor or admin role required")
    approval = session.get(HumanApproval, approval_id)
    if approval is None:
        raise HTTPException(status_code=404, detail="Approval not found")
    return _approval_response(approval)


def _approval_response(approval: HumanApproval) -> ApprovalResponse:
    return ApprovalResponse(
        approval_id=approval.id,
        thread_id=approval.thread_id,
        status="executed" if approval.consumed else approval.status,
        action_type=approval.action_type,
        action_payload=json.loads(approval.action_payload)["payload"],
        expires_at=approval.expires_at.isoformat() if approval.expires_at else None,
    )


@router.post("/approvals/{approval_id}/decisions", response_model=WorkflowResponse)
async def decide_approval(
    approval_id: int,
    payload: ApprovalDecisionRequest,
    actor: Annotated[tuple[int, str], Depends(get_verified_actor)],
    session: Annotated[Session, Depends(get_support_db)],
    workflow: Annotated[SupportWorkflow, Depends(get_workflow)],
) -> WorkflowResponse:
    if actor[1] not in {"supervisor", "admin"}:
        raise HTTPException(status_code=403, detail="Supervisor or admin role required")
    existing = session.get(HumanApproval, approval_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Approval not found")
    snapshot = await workflow.graph.aget_state(
        {"configurable": {"thread_id": existing.thread_id}}
    )
    checkpoint_approval_id = (
        snapshot.values.get("approval_id") if snapshot.values else None
    )
    checkpoint_approval = (
        session.get(HumanApproval, checkpoint_approval_id)
        if checkpoint_approval_id
        else None
    )
    is_replacement = (
        checkpoint_approval is not None
        and checkpoint_approval.thread_id == existing.thread_id
        and checkpoint_approval.status == "rejected"
    )
    if not snapshot.values or (
        checkpoint_approval_id != approval_id and not is_replacement
    ):
        raise HTTPException(
            status_code=409, detail="Workflow checkpoint is missing or mismatched"
        )
    try:
        approval = ApprovalService(session).decide(approval_id, payload, actor[0])
        thread_id = approval.thread_id
        if payload.edited_action is not None:
            replacement = ApprovalService(session).request(
                thread_id=thread_id,
                draft=payload.edited_action,
                ticket_id=payload.edited_action.payload.get("ticket_id"),
            )
        session.commit()
    except ApprovalError as error:
        session.rollback()
        error_status = (
            status.HTTP_403_FORBIDDEN
            if "role required" in str(error)
            else status.HTTP_409_CONFLICT
        )
        raise HTTPException(status_code=error_status, detail=str(error)) from error
    if payload.edited_action is not None:
        resolution = SupportResolution.model_validate(snapshot.values["resolution"])
        return WorkflowResponse(
            thread_id=thread_id,
            status="approval_pending",
            resolution=resolution.model_copy(
                update={"ticket_draft": payload.edited_action}
            ),
            approval_id=replacement.id,
            workflow_mode=(
                "deep_agent"
                if snapshot.values.get("complexity") == "investigation"
                else "deterministic"
            ),
        )
    update: dict = {
        "principal": GatewayPrincipal(
            subject=f"user:{actor[0]}", role=actor[1], actor_id=actor[0]
        ).model_dump()
    }
    # A replacement approval created by a prior edit resumes the original
    # checkpoint with the newly authorized ID and exact action.
    if snapshot.values.get("approval_id") != approval_id:
        resolution = SupportResolution.model_validate(snapshot.values["resolution"])
        encoded = json.loads(approval.action_payload)
        update["approval_id"] = approval_id
        update["resolution"] = resolution.model_copy(
            update={"ticket_draft": encoded}
        ).model_dump()
    result = await workflow.graph.ainvoke(
        Command(resume={"decision": payload.decision}, update=update),
        {"configurable": {"thread_id": thread_id}},
    )
    return _response(thread_id, result)
