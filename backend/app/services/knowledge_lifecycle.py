"""Transactional knowledge lifecycle with fail-closed promotion."""

import hashlib
from datetime import UTC, datetime
from uuid import NAMESPACE_URL, uuid5

from langchain_core.documents import Document
from qdrant_client import QdrantClient, models
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.knowledge.embeddings import DeterministicTelecomEmbeddings
from backend.app.knowledge.ingestion import ensure_collection, stable_chunk_id
from backend.app.models.audit_event import AuditEvent
from backend.app.models.knowledge_document import KnowledgeDocument
from backend.app.models.knowledge_version import KnowledgeVersion
from backend.app.models.role import Role
from backend.app.models.user import User
from backend.app.schemas.knowledge_admin import (
    KnowledgeUploadRequest,
    KnowledgeVersionResponse,
)
from backend.app.services.approvals import ApprovalError, ApprovalService

ADMIN_ROLES = {"admin", "knowledge_manager"}


class KnowledgeAuthorizationError(PermissionError):
    pass


class KnowledgeConflictError(ValueError):
    pass


def _authorize(role: str) -> None:
    if role not in ADMIN_ROLES:
        raise KnowledgeAuthorizationError("Knowledge administration role required")


def _audit(
    session: Session,
    *,
    actor_id: int,
    action: str,
    resource_id: str,
    outcome: str,
    details: str,
) -> None:
    session.add(
        AuditEvent(
            actor_type="user",
            actor_id=actor_id,
            action=action,
            resource_type="knowledge_version",
            resource_id=resource_id,
            outcome=outcome,
            details=details,
        )
    )


class KnowledgeLifecycleService:
    def __init__(
        self,
        session: Session,
        qdrant: QdrantClient,
        embeddings: DeterministicTelecomEmbeddings,
        collection_name: str,
        *,
        approval_execution_enabled: bool = False,
    ) -> None:
        self.session = session
        self.qdrant = qdrant
        self.embeddings = embeddings
        self.collection_name = collection_name
        self.approval_execution_enabled = approval_execution_enabled

    def upload(
        self, request: KnowledgeUploadRequest, *, actor_id: int, role: str
    ) -> KnowledgeVersionResponse:
        _authorize(role)
        checksum = hashlib.sha256(request.content.encode("utf-8")).hexdigest()
        stable_id = str(uuid5(NAMESPACE_URL, request.metadata.source))
        document = self.session.scalar(
            select(KnowledgeDocument).where(KnowledgeDocument.stable_id == stable_id)
        )
        if document is None:
            document = KnowledgeDocument(
                stable_id=stable_id,
                source=request.metadata.source,
                title=request.metadata.title,
                created_by=actor_id,
            )
            self.session.add(document)
            self.session.flush()

        unchanged = self.session.scalar(
            select(KnowledgeVersion).where(
                KnowledgeVersion.document_id == document.id,
                KnowledgeVersion.checksum == checksum,
            )
        )
        if unchanged is not None:
            _audit(
                self.session,
                actor_id=actor_id,
                action="knowledge_upload_unchanged",
                resource_id=str(unchanged.id),
                outcome="skipped",
                details=f"checksum={checksum}",
            )
            return self._response(document, unchanged, unchanged=True)

        existing_version = self.session.scalar(
            select(KnowledgeVersion.id).where(
                KnowledgeVersion.document_id == document.id,
                KnowledgeVersion.version == request.version,
            )
        )
        if existing_version is not None:
            raise KnowledgeConflictError(
                "Version label already exists with new content"
            )

        active = self.session.scalar(
            select(KnowledgeVersion)
            .where(
                KnowledgeVersion.document_id == document.id,
                KnowledgeVersion.status == "active",
            )
            .order_by(KnowledgeVersion.id.desc())
        )
        metadata = request.metadata.model_copy(update={"active": False}).model_dump()
        version = KnowledgeVersion(
            document_id=document.id,
            version=request.version,
            checksum=checksum,
            content=request.content,
            metadata_json=metadata,
            status="draft",
            supersedes_id=active.id if active else None,
            created_by=actor_id,
        )
        self.session.add(version)
        self.session.flush()
        _audit(
            self.session,
            actor_id=actor_id,
            action="knowledge_upload",
            resource_id=str(version.id),
            outcome="draft_created",
            details=f"checksum={checksum};version={request.version}",
        )
        return self._response(document, version)

    def promote(
        self,
        version_id: int,
        approval_id: int,
        execution_request_id: str,
        *,
        actor_id: int,
        role: str,
    ) -> KnowledgeVersionResponse:
        if role not in {"supervisor", "admin"}:
            raise KnowledgeAuthorizationError("Supervisor or admin role required")
        if not self.approval_execution_enabled:
            raise KnowledgeAuthorizationError(
                "Knowledge promotion is disabled until verified Phase 9 approval "
                "execution is available"
            )
        database_role = self.session.scalar(
            select(Role.name)
            .join(User, User.role_id == Role.id)
            .where(User.id == actor_id, User.is_active.is_(True))
        )
        if database_role != role:
            raise KnowledgeAuthorizationError("Authenticated promotion actor mismatch")
        version = self.session.scalar(
            select(KnowledgeVersion)
            .where(KnowledgeVersion.id == version_id)
            .with_for_update()
        )
        if version is None:
            raise LookupError("Knowledge version not found")
        if version.promotion_state == "published":
            if version.promotion_request_id != execution_request_id:
                raise KnowledgeConflictError("Knowledge promotion already executed")
            document = self.session.get(KnowledgeDocument, version.document_id)
            assert document is not None
            return self._response(document, version)
        if version.status != "draft" and version.promotion_state != "committed":
            raise KnowledgeConflictError("Only draft knowledge can be promoted")
        document = self.session.get(KnowledgeDocument, version.document_id)
        assert document is not None
        scope = {
            "version_id": version.id,
            "document_id": document.stable_id,
            "version": version.version,
            "checksum": version.checksum,
        }
        if version.promotion_request_id not in (None, execution_request_id):
            raise KnowledgeConflictError("Promotion is owned by another request")
        approval = None
        if version.promotion_state != "committed":
            try:
                approval = ApprovalService(self.session).verify(
                    approval_id=approval_id,
                    operation="promote_knowledge",
                    payload=scope,
                    execution_request_id=execution_request_id,
                )
            except ApprovalError as error:
                _audit(
                    self.session,
                    actor_id=actor_id,
                    action="knowledge_promote",
                    resource_id=str(version.id),
                    outcome="denied",
                    details=type(error).__name__,
                )
                raise KnowledgeAuthorizationError(
                    "Approved exact-scope knowledge promotion required"
                ) from error

        current = self.session.scalar(
            select(KnowledgeVersion).where(
                KnowledgeVersion.document_id == version.document_id,
                KnowledgeVersion.status == "active",
            )
        )
        metadata = {
            **version.metadata_json,
            "active": False,
            "database_version_id": version.id,
            "promotion_request_id": execution_request_id,
        }
        chunk = Document(
            page_content=version.content, metadata={**metadata, "chunk_index": 0}
        )
        point_id = stable_chunk_id(chunk)
        if version.promotion_state == "none":
            version.promotion_state = "staging"
            version.promotion_request_id = execution_request_id
            version.qdrant_point_id = point_id
            version.approval_id = approval_id
            version.promotion_error = None
            self.session.commit()
        try:
            ensure_collection(
                self.qdrant, self.collection_name, self.embeddings.dimensions
            )
            if version.promotion_state in {"staging", "staged"}:
                self.qdrant.upsert(
                    collection_name=self.collection_name,
                    points=[
                        models.PointStruct(
                            id=point_id,
                            vector=self.embeddings.embed_query(version.content),
                            payload={**chunk.metadata, "content": version.content},
                        )
                    ],
                    wait=True,
                )
                version.promotion_state = "staged"
                version.promotion_error = None
                self.session.commit()

                if current is not None:
                    self._set_qdrant_active(current.id, False)
        except Exception as error:
            self.session.rollback()
            version = self.session.get(KnowledgeVersion, version_id)
            if version is not None:
                version.promotion_error = type(error).__name__
                self.session.commit()
            raise

        version = self.session.scalar(
            select(KnowledgeVersion)
            .where(KnowledgeVersion.id == version_id)
            .with_for_update()
        )
        assert version is not None
        if version.promotion_state != "committed":
            current = self.session.scalar(
                select(KnowledgeVersion).where(
                    KnowledgeVersion.document_id == version.document_id,
                    KnowledgeVersion.status == "active",
                    KnowledgeVersion.id != version.id,
                )
            )
            if current is not None:
                current.status = "inactive"
            version.status = "active"
            version.promoted_by = actor_id
            version.promoted_at = datetime.now(UTC)
            version.promotion_state = "committed"
            version.promotion_error = None
            assert approval is not None
            ApprovalService(self.session).consume(approval, execution_request_id)
            _audit(
                self.session,
                actor_id=actor_id,
                action="knowledge_promote_committed",
                resource_id=str(version.id),
                outcome="success",
                details=f"approval_id={approval_id};request_id={execution_request_id}",
            )
            self.session.commit()

        try:
            self._set_qdrant_active(version.id, True)
        except Exception as error:
            self.session.rollback()
            version = self.session.get(KnowledgeVersion, version_id)
            assert version is not None
            version.promotion_error = type(error).__name__
            self.session.commit()
            raise
        version.promotion_state = "published"
        version.promotion_error = None
        _audit(
            self.session,
            actor_id=actor_id,
            action="knowledge_promote_published",
            resource_id=str(version.id),
            outcome="success",
            details=f"approval_id={approval_id};point_id={point_id}",
        )
        self.session.commit()
        return self._response(document, version)

    def _set_qdrant_active(self, version_id: int, active: bool) -> None:
        """Idempotently change visibility for all chunks of one database version."""

        self.qdrant.set_payload(
            collection_name=self.collection_name,
            payload={"active": active},
            points=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="database_version_id",
                            match=models.MatchValue(value=version_id),
                        )
                    ]
                )
            ),
            wait=True,
        )

    def deactivate(
        self, version_id: int, reason: str, *, actor_id: int, role: str
    ) -> KnowledgeVersionResponse:
        _authorize(role)
        version = self.session.get(KnowledgeVersion, version_id)
        if version is None:
            raise LookupError("Knowledge version not found")
        if version.status != "active":
            raise KnowledgeConflictError("Only active knowledge can be deactivated")
        self.qdrant.set_payload(
            collection_name=self.collection_name,
            payload={"active": False},
            points=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="database_version_id",
                            match=models.MatchValue(value=version.id),
                        )
                    ]
                )
            ),
            wait=True,
        )
        version.status = "inactive"
        document = self.session.get(KnowledgeDocument, version.document_id)
        assert document is not None
        _audit(
            self.session,
            actor_id=actor_id,
            action="knowledge_deactivate",
            resource_id=str(version.id),
            outcome="success",
            details=reason,
        )
        return self._response(document, version)

    def reconcile_pending(
        self, *, actor_id: int, role: str, limit: int = 25
    ) -> dict[str, int]:
        """Recover authorized partial promotions without expanding their scope."""

        if role != "admin":
            raise KnowledgeAuthorizationError("Admin role required for reconciliation")
        database_role = self.session.scalar(
            select(Role.name)
            .join(User, User.role_id == Role.id)
            .where(User.id == actor_id, User.is_active.is_(True))
        )
        if database_role != role:
            raise KnowledgeAuthorizationError(
                "Authenticated reconciliation actor mismatch"
            )
        pending = self.session.scalars(
            select(KnowledgeVersion)
            .where(
                KnowledgeVersion.promotion_state.in_(
                    ("staging", "staged", "committed")
                ),
                KnowledgeVersion.approval_id.is_not(None),
                KnowledgeVersion.promotion_request_id.is_not(None),
            )
            .order_by(KnowledgeVersion.id)
            .limit(min(max(limit, 1), 100))
        ).all()
        recovered = failed = 0
        for item in pending:
            try:
                self.promote(
                    item.id,
                    item.approval_id,
                    item.promotion_request_id,
                    actor_id=actor_id,
                    role=role,
                )
                recovered += 1
            except (
                KnowledgeAuthorizationError,
                KnowledgeConflictError,
                LookupError,
                RuntimeError,
                OSError,
                TimeoutError,
            ):
                failed += 1
                self.session.rollback()
        return {"examined": len(pending), "recovered": recovered, "failed": failed}

    @staticmethod
    def _response(
        document: KnowledgeDocument,
        version: KnowledgeVersion,
        *,
        unchanged: bool = False,
    ) -> KnowledgeVersionResponse:
        return KnowledgeVersionResponse(
            document_id=document.id,
            stable_id=document.stable_id,
            version_id=version.id,
            version=version.version,
            checksum=version.checksum,
            status=version.status,
            unchanged=unchanged,
        )
