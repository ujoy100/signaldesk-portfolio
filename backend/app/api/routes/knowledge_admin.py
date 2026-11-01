"""Fail-closed knowledge lifecycle administration endpoints."""

import json
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.auth import AuthenticationError, authenticate_bearer_token
from backend.app.core.oidc import (
    OIDCError,
    authenticate_session,
    authenticated_session_display_name,
)
from backend.app.db.session import get_db
from backend.app.knowledge.client import create_qdrant_client
from backend.app.knowledge.embeddings import DeterministicTelecomEmbeddings
from backend.app.knowledge.retrieval import TelecomRetriever
from backend.app.mcp.contracts import (
    GatewayPrincipal,
    KnowledgePromotionOutput,
)
from backend.app.mcp.gateway import MCPGateway, create_database_audit_writer
from backend.app.mcp.knowledge_server import create_knowledge_server
from backend.app.models.human_approval import HumanApproval
from backend.app.models.knowledge_document import KnowledgeDocument
from backend.app.models.knowledge_version import KnowledgeVersion
from backend.app.models.role import Role
from backend.app.models.user import User
from backend.app.schemas.knowledge_admin import (
    KnowledgeDeactivationRequest,
    KnowledgePromotionApprovalRequest,
    KnowledgePromotionRequest,
    KnowledgeUploadRequest,
    KnowledgeVersionResponse,
)
from backend.app.schemas.support import (
    ApprovalDecisionRequest,
    ApprovalResponse,
)
from backend.app.services.approvals import ApprovalError, ApprovalService
from backend.app.services.knowledge_lifecycle import (
    KnowledgeAuthorizationError,
    KnowledgeConflictError,
    KnowledgeLifecycleService,
)

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge-admin"])


def get_actor(
    request: Request,
    authorization: Annotated[str | None, Header(alias="Authorization")] = None,
) -> tuple[int, str]:
    """Authenticate a server session, or a non-production development JWT."""

    settings = request.app.state.settings
    session_token = request.cookies.get(settings.session_cookie_name)
    if session_token:
        engine = create_engine(settings.database_url, pool_pre_ping=True)
        try:
            with Session(engine) as session:
                actor = authenticate_session(
                    session,
                    session_token,
                    request.headers.get("X-CSRF-Token"),
                    require_csrf=request.method not in {"GET", "HEAD", "OPTIONS"},
                )
                request.state.auth_display_name = authenticated_session_display_name(
                    session, session_token
                )
                return actor
        except OIDCError as error:
            raise HTTPException(status_code=401, detail=str(error)) from error
        finally:
            engine.dispose()

    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    if settings.app_env == "production":
        raise HTTPException(
            status_code=401, detail="Bearer development access disabled"
        )
    try:
        principal = authenticate_bearer_token(
            authorization.removeprefix("Bearer "), settings
        )
    except AuthenticationError as error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(error)
        ) from error
    request.state.auth_display_name = "Development user"
    return principal.actor_id, principal.role


def get_lifecycle_service(
    request: Request, session: Annotated[Session, Depends(get_db)]
) -> KnowledgeLifecycleService:
    settings = request.app.state.settings
    return KnowledgeLifecycleService(
        session,
        create_qdrant_client(settings),
        DeterministicTelecomEmbeddings(settings.embedding_dimensions),
        settings.qdrant_collection,
        approval_execution_enabled=True,
    )


def _translate_error(error: Exception) -> HTTPException:
    if isinstance(error, KnowledgeAuthorizationError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error))
    if isinstance(error, KnowledgeConflictError):
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))
    if isinstance(error, LookupError):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Knowledge operation failed",
    )


def _promotion_scope(document: KnowledgeDocument, version: KnowledgeVersion) -> dict:
    return {
        "version_id": version.id,
        "document_id": document.stable_id,
        "version": version.version,
        "checksum": version.checksum,
    }


def _approval_response(approval: HumanApproval) -> ApprovalResponse:
    return ApprovalResponse(
        approval_id=approval.id,
        thread_id=approval.thread_id,
        status="executed" if approval.consumed else approval.status,
        action_type=approval.action_type,
        action_payload=json.loads(approval.action_payload)["payload"],
        expires_at=approval.expires_at.isoformat() if approval.expires_at else None,
    )


@router.post(
    "/versions/{version_id}/promotion-requests",
    response_model=ApprovalResponse,
    status_code=201,
)
def request_knowledge_promotion(
    version_id: int,
    payload: KnowledgePromotionApprovalRequest,
    actor: Annotated[tuple[int, str], Depends(get_actor)],
    service: Annotated[KnowledgeLifecycleService, Depends(get_lifecycle_service)],
) -> ApprovalResponse:
    if actor[1] not in {"knowledge_manager", "admin"}:
        raise HTTPException(
            status_code=403, detail="Knowledge administration role required"
        )
    database_role = service.session.scalar(
        select(Role.name)
        .join(User, User.role_id == Role.id)
        .where(User.id == actor[0], User.is_active.is_(True))
    )
    if database_role != actor[1]:
        raise HTTPException(status_code=403, detail="Authenticated identity mismatch")
    version = service.session.get(KnowledgeVersion, version_id)
    if version is None:
        raise HTTPException(status_code=404, detail="Knowledge version not found")
    if version.status != "draft":
        raise HTTPException(
            status_code=409, detail="Only draft knowledge can be promoted"
        )
    document = service.session.get(KnowledgeDocument, version.document_id)
    assert document is not None
    approval = ApprovalService(service.session).request_action(
        thread_id=payload.thread_id,
        operation="promote_knowledge",
        payload=_promotion_scope(document, version),
    )
    service.session.commit()
    return _approval_response(approval)


@router.post(
    "/promotion-approvals/{approval_id}/decisions",
    response_model=ApprovalResponse,
)
def decide_knowledge_promotion(
    approval_id: int,
    payload: ApprovalDecisionRequest,
    actor: Annotated[tuple[int, str], Depends(get_actor)],
    service: Annotated[KnowledgeLifecycleService, Depends(get_lifecycle_service)],
) -> ApprovalResponse:
    if actor[1] not in {"supervisor", "admin"}:
        raise HTTPException(status_code=403, detail="Supervisor or admin role required")
    try:
        approval = ApprovalService(service.session).decide(
            approval_id, payload, actor[0]
        )
        if approval.action_type != "promote_knowledge":
            raise ApprovalError("approval action mismatch")
        service.session.commit()
        return _approval_response(approval)
    except ApprovalError as error:
        service.session.rollback()
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.post("/versions", response_model=KnowledgeVersionResponse, status_code=201)
def upload_knowledge(
    payload: KnowledgeUploadRequest,
    actor: Annotated[tuple[int, str], Depends(get_actor)],
    service: Annotated[KnowledgeLifecycleService, Depends(get_lifecycle_service)],
) -> KnowledgeVersionResponse:
    try:
        response = service.upload(payload, actor_id=actor[0], role=actor[1])
        service.session.commit()
        return response
    except Exception as error:
        service.session.rollback()
        raise _translate_error(error) from error


@router.post("/versions/{version_id}/promote", response_model=KnowledgeVersionResponse)
async def promote_knowledge(
    version_id: int,
    payload: KnowledgePromotionRequest,
    actor: Annotated[tuple[int, str], Depends(get_actor)],
    service: Annotated[KnowledgeLifecycleService, Depends(get_lifecycle_service)],
) -> KnowledgeVersionResponse:
    try:
        version = service.session.get(KnowledgeVersion, version_id)
        if version is None:
            raise LookupError("Knowledge version not found")
        document = service.session.get(KnowledgeDocument, version.document_id)
        assert document is not None
        factory = sessionmaker(bind=service.session.get_bind(), expire_on_commit=False)

        def execute(**arguments: object) -> KnowledgePromotionOutput:
            with factory() as execution_session:
                execution_service = KnowledgeLifecycleService(
                    execution_session,
                    service.qdrant,
                    service.embeddings,
                    service.collection_name,
                    approval_execution_enabled=True,
                )
                result = execution_service.promote(
                    int(arguments["version_id"]),
                    int(arguments["approval_id"]),
                    str(arguments["execution_request_id"]),
                    actor_id=actor[0],
                    role=actor[1],
                )
                persisted = execution_session.get(KnowledgeVersion, result.version_id)
                assert persisted is not None
                return KnowledgePromotionOutput(
                    executed=True,
                    version_id=result.version_id,
                    status=result.status,
                    promotion_state=persisted.promotion_state,
                )

        retriever = TelecomRetriever(
            service.qdrant,
            service.collection_name,
            service.embeddings,
        )
        gateway = MCPGateway(
            {
                "knowledge": create_knowledge_server(
                    retriever, promotion_handler=execute
                )
            },
            approval_session_factory=factory,
            audit_writer=create_database_audit_writer(factory),
        )
        gateway_response = await gateway.invoke(
            "knowledge",
            "promote_knowledge",
            _promotion_scope(document, version),
            GatewayPrincipal(
                subject=f"user:{actor[0]}", role=actor[1], actor_id=actor[0]
            ),
            approval_id=payload.approval_id,
            execution_request_id=payload.execution_request_id,
        )
        if not gateway_response.allowed or not gateway_response.result:
            raise KnowledgeAuthorizationError("Gateway denied knowledge promotion")
        refreshed = service.session.get(KnowledgeVersion, version_id)
        service.session.refresh(refreshed)
        return service._response(document, refreshed)
    except Exception as error:
        service.session.rollback()
        raise _translate_error(error) from error


@router.post(
    "/versions/{version_id}/deactivate", response_model=KnowledgeVersionResponse
)
def deactivate_knowledge(
    version_id: int,
    payload: KnowledgeDeactivationRequest,
    actor: Annotated[tuple[int, str], Depends(get_actor)],
    service: Annotated[KnowledgeLifecycleService, Depends(get_lifecycle_service)],
) -> KnowledgeVersionResponse:
    try:
        response = service.deactivate(
            version_id,
            payload.reason,
            actor_id=actor[0],
            role=actor[1],
        )
        service.session.commit()
        return response
    except Exception as error:
        service.session.rollback()
        raise _translate_error(error) from error
