"""PostgreSQL/Qdrant knowledge lifecycle integration tests."""

from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from qdrant_client import QdrantClient
from sqlalchemy import Connection, delete, select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.knowledge.embeddings import DeterministicTelecomEmbeddings
from backend.app.knowledge.models import KnowledgeMetadata
from backend.app.models.audit_event import AuditEvent
from backend.app.models.human_approval import HumanApproval
from backend.app.models.knowledge_document import KnowledgeDocument
from backend.app.models.knowledge_version import KnowledgeVersion
from backend.app.models.role import Role
from backend.app.models.subscription import Subscription  # noqa: F401
from backend.app.models.ticket import Ticket  # noqa: F401
from backend.app.models.user import User
from backend.app.schemas.knowledge_admin import KnowledgeUploadRequest
from backend.app.schemas.support import ApprovalDecisionRequest
from backend.app.services.approvals import ApprovalService
from backend.app.services.knowledge_lifecycle import (
    KnowledgeAuthorizationError,
    KnowledgeConflictError,
    KnowledgeLifecycleService,
)


def _service(connection: Connection) -> tuple[KnowledgeLifecycleService, Session]:
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    client = QdrantClient(location=":memory:")
    return (
        KnowledgeLifecycleService(
            session,
            client,
            DeterministicTelecomEmbeddings(128),
            "lifecycle_test",
            approval_execution_enabled=True,
        ),
        session,
    )


def _actor(session: Session) -> User:
    suffix = uuid4().hex[:10]
    role = session.scalar(select(Role).where(Role.name == "admin"))
    if role is None:
        role = Role(name="admin")
        session.add(role)
        session.flush()
    user = User(
        email=f"manager-{suffix}@example.test",
        full_name="Fictional Knowledge Manager",
        role_id=role.id,
    )
    session.add(user)
    session.flush()
    return user


def _upload(version: str = "1.0", content: str | None = None) -> KnowledgeUploadRequest:
    return KnowledgeUploadRequest(
        version=version,
        media_type="text/markdown",
        content=content
        or "Fictional policy LIFE-CYCLE-01 explains safe lifecycle testing.",
        metadata=KnowledgeMetadata(
            document_id="lifecycle-policy-001",
            source="fictional://telecom/policies/lifecycle",
            service="knowledge",
            category="policy",
            version=version,
            active=False,
            access_roles=["public", "support_agent"],
            page=1,
            section="Lifecycle",
            title="Fictional lifecycle policy",
        ),
    )


def _approved(session: Session, version_id: int, reviewer_id: int) -> HumanApproval:
    version = session.get(KnowledgeVersion, version_id)
    document = session.get(KnowledgeDocument, version.document_id)
    approval = ApprovalService(session).request_action(
        thread_id=f"knowledge-{uuid4()}",
        operation="promote_knowledge",
        payload={
            "version_id": version.id,
            "document_id": document.stable_id,
            "version": version.version,
            "checksum": version.checksum,
        },
    )
    ApprovalService(session).decide(
        approval.id, ApprovalDecisionRequest(decision="approve"), reviewer_id
    )
    return approval


def test_upload_duplicate_and_authorization(test_db_connection: Connection) -> None:
    service, session = _service(test_db_connection)
    actor = _actor(session)

    with pytest.raises(KnowledgeAuthorizationError):
        service.upload(_upload(), actor_id=actor.id, role="support_agent")

    first = service.upload(_upload(), actor_id=actor.id, role="admin")
    duplicate = service.upload(_upload(), actor_id=actor.id, role="admin")

    assert first.status == "draft"
    assert duplicate.unchanged
    assert duplicate.version_id == first.version_id


def test_incremental_promotion_deactivates_superseded_version(
    test_db_connection: Connection,
) -> None:
    service, session = _service(test_db_connection)
    actor = _actor(session)
    first = service.upload(_upload(), actor_id=actor.id, role="admin")

    with pytest.raises(KnowledgeAuthorizationError):
        service.promote(
            first.version_id,
            approval_id=999999,
            execution_request_id="missing-approval",
            actor_id=actor.id,
            role="admin",
        )

    first_approval = _approved(session, first.version_id, actor.id)
    active_first = service.promote(
        first.version_id,
        first_approval.id,
        "promote-first",
        actor_id=actor.id,
        role="admin",
    )
    second = service.upload(
        _upload("2.0", "Updated fictional policy LIFE-CYCLE-02 with new guidance."),
        actor_id=actor.id,
        role="admin",
    )
    second_approval = _approved(session, second.version_id, actor.id)
    active_second = service.promote(
        second.version_id,
        second_approval.id,
        "promote-second",
        actor_id=actor.id,
        role="admin",
    )

    assert active_first.status == "active"
    assert active_second.status == "active"
    statuses = dict(
        session.execute(
            select(KnowledgeVersion.version, KnowledgeVersion.status).where(
                KnowledgeVersion.document_id == second.document_id
            )
        ).all()
    )
    assert statuses == {"1.0": "inactive", "2.0": "active"}
    records, _ = service.qdrant.scroll(
        service.collection_name,
        limit=10,
        with_payload=True,
    )
    active_versions = [
        record.payload["version"] for record in records if record.payload["active"]
    ]
    assert active_versions == ["2.0"]


def test_deactivation_and_qdrant_failure_rollback(
    test_db_connection: Connection,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    service, session = _service(test_db_connection)
    actor = _actor(session)
    version = service.upload(_upload(), actor_id=actor.id, role="admin")
    approval = _approved(session, version.version_id, actor.id)

    def fail_upsert(*args, **kwargs):
        raise RuntimeError("simulated qdrant failure")

    monkeypatch.setattr(service.qdrant, "upsert", fail_upsert)
    with pytest.raises(RuntimeError, match="simulated"):
        service.promote(
            version.version_id,
            approval.id,
            "failure-request",
            actor_id=actor.id,
            role="admin",
        )
    persisted = session.get(KnowledgeVersion, version.version_id)
    assert persisted.status == "draft"
    assert persisted.promotion_state == "staging"
    assert persisted.promotion_error == "RuntimeError"
    if service.qdrant.collection_exists(service.collection_name):
        records, _ = service.qdrant.scroll(
            service.collection_name, limit=10, with_payload=True
        )
        assert not any(record.payload.get("active") for record in records)
    assert session.get(HumanApproval, approval.id).consumed is False


def test_publish_failure_recovers_idempotently_without_early_visibility(
    test_db_connection: Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    service, session = _service(test_db_connection)
    actor = _actor(session)
    version = service.upload(_upload(), actor_id=actor.id, role="admin")
    approval = _approved(session, version.version_id, actor.id)
    original_set_payload = service.qdrant.set_payload

    def fail_publish(*args, **kwargs):
        if kwargs.get("payload") == {"active": True}:
            raise RuntimeError("simulated publish failure")
        return original_set_payload(*args, **kwargs)

    monkeypatch.setattr(service.qdrant, "set_payload", fail_publish)
    with pytest.raises(RuntimeError, match="publish"):
        service.promote(
            version.version_id,
            approval.id,
            "recoverable-publish",
            actor_id=actor.id,
            role="admin",
        )
    committed = session.get(KnowledgeVersion, version.version_id)
    assert committed.status == "active"
    assert committed.promotion_state == "committed"
    records, _ = service.qdrant.scroll(
        service.collection_name, limit=10, with_payload=True
    )
    assert not any(record.payload.get("active") for record in records)

    monkeypatch.setattr(service.qdrant, "set_payload", original_set_payload)
    version_id, approval_id, actor_id = version.version_id, approval.id, actor.id
    session.close()
    reconstructed_session = Session(
        bind=test_db_connection, join_transaction_mode="create_savepoint"
    )
    reconstructed = KnowledgeLifecycleService(
        reconstructed_session,
        service.qdrant,
        service.embeddings,
        service.collection_name,
        approval_execution_enabled=True,
    )
    reconciliation = reconstructed.reconcile_pending(actor_id=actor_id, role="admin")
    assert reconciliation == {"examined": 1, "recovered": 1, "failed": 0}
    assert (
        reconstructed_session.get(KnowledgeVersion, version_id).promotion_state
        == "published"
    )
    records, _ = reconstructed.qdrant.scroll(
        reconstructed.collection_name, limit=10, with_payload=True
    )
    assert [
        record.payload["version"] for record in records if record.payload["active"]
    ] == ["1.0"]

    repeated = reconstructed.promote(
        version_id,
        approval_id,
        "recoverable-publish",
        actor_id=actor_id,
        role="admin",
    )
    assert repeated.version_id == version_id
    with pytest.raises(KnowledgeConflictError, match="already executed"):
        reconstructed.promote(
            version_id,
            approval_id,
            "forged-replay-request",
            actor_id=actor_id,
            role="admin",
        )
    reconstructed_session.close()


def test_concurrent_promotions_have_one_owner(test_db_engine) -> None:
    factory = sessionmaker(bind=test_db_engine, expire_on_commit=False)
    qdrant = QdrantClient(location=":memory:")
    embeddings = DeterministicTelecomEmbeddings(128)
    collection = f"concurrent_promotion_{uuid4().hex}"
    with factory() as session:
        service = KnowledgeLifecycleService(
            session, qdrant, embeddings, collection, approval_execution_enabled=True
        )
        actor = _actor(session)
        version = service.upload(_upload(), actor_id=actor.id, role="admin")
        approval = _approved(session, version.version_id, actor.id)
        session.commit()
        actor_id, version_id = actor.id, version.version_id
        document_id, approval_id = version.document_id, approval.id

    def promote(request_id: str) -> str:
        with factory() as session:
            service = KnowledgeLifecycleService(
                session,
                qdrant,
                embeddings,
                collection,
                approval_execution_enabled=True,
            )
            try:
                service.promote(
                    version_id,
                    approval_id,
                    request_id,
                    actor_id=actor_id,
                    role="admin",
                )
                return "published"
            except (KnowledgeConflictError, KnowledgeAuthorizationError):
                session.rollback()
                return "denied"

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(promote, ["concurrent-one", "concurrent-two"]))
        assert sorted(results) == ["denied", "published"]
        with factory() as session:
            assert (
                session.get(KnowledgeVersion, version_id).promotion_state == "published"
            )
            assert session.get(HumanApproval, approval_id).consumed is True
    finally:
        with factory() as session, session.begin():
            session.execute(
                delete(AuditEvent).where(
                    (
                        (AuditEvent.resource_type == "knowledge_version")
                        & (AuditEvent.resource_id == str(version_id))
                    )
                    | (
                        (AuditEvent.resource_type == "human_approval")
                        & (AuditEvent.resource_id == str(approval_id))
                    )
                )
            )
            session.execute(
                delete(KnowledgeVersion).where(KnowledgeVersion.id == version_id)
            )
            session.execute(
                delete(HumanApproval).where(HumanApproval.id == approval_id)
            )
            session.execute(
                delete(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
            )
            session.execute(delete(User).where(User.id == actor_id))


def test_mismatched_and_unauthorized_promotion_fail_closed(
    test_db_connection: Connection,
) -> None:
    service, session = _service(test_db_connection)
    actor = _actor(session)
    first = service.upload(_upload(), actor_id=actor.id, role="admin")
    approval = _approved(session, first.version_id, actor.id)
    second = service.upload(
        _upload("2.0", "Different fictional knowledge content for mismatch testing."),
        actor_id=actor.id,
        role="admin",
    )
    with pytest.raises(KnowledgeAuthorizationError):
        service.promote(
            second.version_id,
            approval.id,
            "mismatched-scope",
            actor_id=actor.id,
            role="admin",
        )
    with pytest.raises(KnowledgeAuthorizationError, match="Supervisor"):
        service.promote(
            first.version_id,
            approval.id,
            "unauthorized-role",
            actor_id=actor.id,
            role="knowledge_manager",
        )
    assert session.get(KnowledgeVersion, first.version_id).status == "draft"
    assert session.get(KnowledgeVersion, second.version_id).status == "draft"


def test_postgresql_commit_failure_leaves_safe_retryable_state(
    test_db_connection: Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    service, session = _service(test_db_connection)
    actor = _actor(session)
    version = service.upload(_upload(), actor_id=actor.id, role="admin")
    approval = _approved(session, version.version_id, actor.id)
    original_commit = session.commit
    commits = 0

    def fail_authority_commit() -> None:
        nonlocal commits
        commits += 1
        if commits == 3:
            raise RuntimeError("simulated PostgreSQL commit failure")
        original_commit()

    monkeypatch.setattr(session, "commit", fail_authority_commit)
    with pytest.raises(RuntimeError, match="PostgreSQL"):
        service.promote(
            version.version_id,
            approval.id,
            "postgres-recovery",
            actor_id=actor.id,
            role="admin",
        )
    session.rollback()
    persisted = session.get(KnowledgeVersion, version.version_id)
    assert persisted.status == "draft"
    assert persisted.promotion_state == "staged"
    records, _ = service.qdrant.scroll(
        service.collection_name, limit=10, with_payload=True
    )
    assert not any(record.payload.get("active") for record in records)
    assert session.get(HumanApproval, approval.id).consumed is False

    monkeypatch.setattr(session, "commit", original_commit)
    recovered = service.promote(
        version.version_id,
        approval.id,
        "postgres-recovery",
        actor_id=actor.id,
        role="admin",
    )
    assert recovered.status == "active"
    assert (
        session.get(KnowledgeVersion, version.version_id).promotion_state == "published"
    )
