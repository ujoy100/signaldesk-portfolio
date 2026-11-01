"""Authenticated read-only operational views for the React application."""

import json
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.routes.support import get_support_db, get_verified_actor
from backend.app.models.conversation import Conversation
from backend.app.models.evaluation_run import EvaluationRun
from backend.app.models.feedback import Feedback
from backend.app.models.human_approval import HumanApproval
from backend.app.models.knowledge_version import KnowledgeVersion
from backend.app.models.ticket import Ticket
from backend.app.schemas.operations import (
    ApprovalListItem,
    EvaluationRunView,
    FeedbackCreate,
    FeedbackView,
    KnowledgeVersionListItem,
    SessionInfo,
)

router = APIRouter(prefix="/api/v1", tags=["operations"])


@router.get("/session", response_model=SessionInfo)
def session_info(
    request: Request,
    actor: Annotated[tuple[int, str], Depends(get_verified_actor)],
) -> SessionInfo:
    return SessionInfo(
        actor_id=actor[0],
        role=actor[1],
        display_name=getattr(request.state, "auth_display_name", "Microsoft user"),
    )


@router.get("/approvals", response_model=list[ApprovalListItem])
def list_approvals(
    actor: Annotated[tuple[int, str], Depends(get_verified_actor)],
    session: Annotated[Session, Depends(get_support_db)],
) -> list[ApprovalListItem]:
    if actor[1] not in {"supervisor", "admin"}:
        raise HTTPException(status_code=403, detail="Supervisor or admin role required")
    approvals = session.scalars(
        select(HumanApproval).order_by(HumanApproval.id.desc()).limit(50)
    ).all()
    return [
        ApprovalListItem(
            id=item.id,
            thread_id=item.thread_id,
            status="executed" if item.consumed else item.status,
            action_type=item.action_type,
            action_payload=json.loads(item.action_payload)["payload"],
            consumed=item.consumed,
            action_description=item.action_description,
            expires_at=item.expires_at.isoformat() if item.expires_at else None,
            ticket_number=(
                ticket.ticket_number
                if (ticket := session.get(Ticket, item.ticket_id))
                else None
            ),
            current_ticket_status=ticket.status if ticket else None,
            current_ticket_priority=ticket.priority if ticket else None,
        )
        for item in approvals
    ]


@router.post(
    "/feedback", response_model=FeedbackView, status_code=status.HTTP_201_CREATED
)
def submit_feedback(
    payload: FeedbackCreate,
    _actor: Annotated[tuple[int, str], Depends(get_verified_actor)],
    session: Annotated[Session, Depends(get_support_db)],
) -> FeedbackView:
    conversation = session.scalar(
        select(Conversation).where(Conversation.session_id == payload.thread_id)
    )
    if conversation is None:
        conversation = Conversation(
            session_id=payload.thread_id,
            customer_id=payload.customer_id,
            channel="web",
            status="active",
        )
        session.add(conversation)
        session.flush()
    elif (
        payload.customer_id is not None
        and conversation.customer_id != payload.customer_id
    ):
        raise HTTPException(status_code=409, detail="Feedback customer scope mismatch")
    feedback = Feedback(
        conversation_id=conversation.id,
        customer_id=payload.customer_id,
        rating=payload.rating,
        comment=payload.comment,
    )
    session.add(feedback)
    session.commit()
    return FeedbackView(
        id=feedback.id,
        thread_id=conversation.session_id,
        rating=feedback.rating,
        comment=feedback.comment,
    )


@router.get("/feedback", response_model=list[FeedbackView])
def list_feedback(
    actor: Annotated[tuple[int, str], Depends(get_verified_actor)],
    session: Annotated[Session, Depends(get_support_db)],
) -> list[FeedbackView]:
    if actor[1] not in {"supervisor", "admin"}:
        raise HTTPException(status_code=403, detail="Supervisor or admin role required")
    rows = session.execute(
        select(Feedback, Conversation.session_id)
        .join(Conversation, Feedback.conversation_id == Conversation.id)
        .order_by(Feedback.id.desc())
        .limit(50)
    ).all()
    return [
        FeedbackView(
            id=feedback.id,
            thread_id=thread_id,
            rating=feedback.rating,
            comment=feedback.comment,
        )
        for feedback, thread_id in rows
    ]


@router.get("/evaluations", response_model=list[EvaluationRunView])
def list_evaluations(
    actor: Annotated[tuple[int, str], Depends(get_verified_actor)],
    session: Annotated[Session, Depends(get_support_db)],
) -> list[EvaluationRunView]:
    if actor[1] not in {"supervisor", "admin"}:
        raise HTTPException(status_code=403, detail="Supervisor or admin role required")
    runs = session.scalars(
        select(EvaluationRun).order_by(EvaluationRun.id.desc()).limit(50)
    ).all()
    return [
        EvaluationRunView(
            id=item.id,
            evaluation_type=item.evaluation_type,
            dataset_name=item.dataset_name,
            model_name=item.model_name,
            status=item.status,
            configuration=item.configuration,
        )
        for item in runs
    ]


@router.get("/knowledge/versions", response_model=list[KnowledgeVersionListItem])
def list_knowledge_versions(
    actor: Annotated[tuple[int, str], Depends(get_verified_actor)],
    session: Annotated[Session, Depends(get_support_db)],
) -> list[KnowledgeVersionListItem]:
    if actor[1] != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    versions = session.scalars(
        select(KnowledgeVersion).order_by(KnowledgeVersion.id.desc()).limit(100)
    ).all()
    return [
        KnowledgeVersionListItem(
            id=item.id,
            document_id=item.document_id,
            version=item.version,
            status=item.status,
            promotion_state=item.promotion_state,
            promotion_error=item.promotion_error,
        )
        for item in versions
    ]
