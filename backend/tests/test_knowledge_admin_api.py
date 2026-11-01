"""Knowledge administration API security tests."""

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from fastapi.testclient import TestClient
from qdrant_client import QdrantClient
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from backend.app.api.routes.knowledge_admin import get_lifecycle_service
from backend.app.core.config import Settings
from backend.app.knowledge.embeddings import DeterministicTelecomEmbeddings
from backend.app.knowledge.models import KnowledgeMetadata
from backend.app.main import create_app
from backend.app.models.audit_event import AuditEvent
from backend.app.models.human_approval import HumanApproval
from backend.app.models.knowledge_document import KnowledgeDocument
from backend.app.models.knowledge_version import KnowledgeVersion
from backend.app.models.role import Role
from backend.app.models.subscription import Subscription  # noqa: F401
from backend.app.models.ticket import Ticket  # noqa: F401
from backend.app.models.user import User
from backend.app.schemas.knowledge_admin import KnowledgeUploadRequest
from backend.app.services.knowledge_lifecycle import KnowledgeLifecycleService

SECRET = "knowledge-api-test-secret-with-sufficient-entropy"
AUDIENCE = "knowledge-api-tests"


def _token(actor_id: int, role: str) -> str:
    return jwt.encode(
        {
            "sub": f"knowledge-{actor_id}",
            "actor_id": actor_id,
            "role": role,
            "aud": AUDIENCE,
            "exp": datetime.now(UTC) + timedelta(minutes=5),
        },
        SECRET,
        algorithm="HS256",
    )


def _role_user(session: Session, role_name: str) -> User:
    role = session.scalar(select(Role).where(Role.name == role_name))
    if role is None:
        role = Role(name=role_name)
        session.add(role)
        session.flush()
    user = User(
        email=f"knowledge-api-{uuid4()}@example.test",
        full_name="Knowledge API Actor",
        role_id=role.id,
    )
    session.add(user)
    session.flush()
    return user


def test_knowledge_upload_requires_authentication() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/v1/knowledge/versions",
        json={
            "version": "1.0",
            "media_type": "text/plain",
            "content": "A fictional document long enough to pass validation.",
            "metadata": {
                "document_id": "api-test-001",
                "source": "fictional://api/test",
                "service": "mobile",
                "category": "test",
                "version": "1.0",
                "active": False,
                "access_roles": ["public"],
                "page": 1,
                "section": "Test",
                "title": "API test",
            },
        },
    )

    assert response.status_code == 401


def test_authenticated_knowledge_approval_and_gateway_promotion(test_db_engine) -> None:
    factory = sessionmaker(bind=test_db_engine, expire_on_commit=False)
    qdrant = QdrantClient(location=":memory:")
    embeddings = DeterministicTelecomEmbeddings(128)
    collection = f"knowledge_api_{uuid4().hex}"
    with factory() as session:
        admin = _role_user(session, "admin")
        supervisor = _role_user(session, "supervisor")
        service = KnowledgeLifecycleService(
            session, qdrant, embeddings, collection, approval_execution_enabled=True
        )
        upload = KnowledgeUploadRequest(
            version="1.0",
            media_type="text/markdown",
            content="Fictional API promotion policy with enough content for testing.",
            metadata=KnowledgeMetadata(
                document_id="api-promotion-policy",
                source=f"fictional://promotion/{uuid4()}",
                service="knowledge",
                category="policy",
                version="1.0",
                active=False,
                access_roles=["public"],
                page=1,
                section="Promotion",
                title="API promotion policy",
            ),
        )
        version = service.upload(upload, actor_id=admin.id, role="admin")
        session.commit()
        admin_id, supervisor_id = admin.id, supervisor.id
        version_id, document_id = version.version_id, version.document_id

    def override_service() -> Iterator[KnowledgeLifecycleService]:
        with factory() as session:
            yield KnowledgeLifecycleService(
                session,
                qdrant,
                embeddings,
                collection,
                approval_execution_enabled=True,
            )

    app = create_app(
        Settings(
            _env_file=None,
            app_env="testing",
            auth_jwt_secret=SECRET,
            auth_jwt_audience=AUDIENCE,
        )
    )
    app.dependency_overrides[get_lifecycle_service] = override_service
    client = TestClient(app)
    try:
        requested = client.post(
            f"/api/v1/knowledge/versions/{version_id}/promotion-requests",
            headers={"Authorization": f"Bearer {_token(admin_id, 'admin')}"},
            json={"thread_id": f"knowledge-api-{uuid4()}"},
        )
        assert requested.status_code == 201, requested.text
        approval_id = requested.json()["approval_id"]
        decided = client.post(
            f"/api/v1/knowledge/promotion-approvals/{approval_id}/decisions",
            headers={"Authorization": f"Bearer {_token(supervisor_id, 'supervisor')}"},
            json={"decision": "approve"},
        )
        assert decided.status_code == 200, decided.text
        promoted = client.post(
            f"/api/v1/knowledge/versions/{version_id}/promote",
            headers={"Authorization": f"Bearer {_token(supervisor_id, 'supervisor')}"},
            json={
                "approval_id": approval_id,
                "execution_request_id": f"api-execution-{uuid4()}",
            },
        )
        assert promoted.status_code == 200, promoted.text
        assert promoted.json()["status"] == "active"
        records, _ = qdrant.scroll(collection, limit=10, with_payload=True)
        assert len([record for record in records if record.payload["active"]]) == 1
    finally:
        with factory() as session, session.begin():
            approval_ids = session.scalars(
                select(HumanApproval.id).where(
                    HumanApproval.action_type == "promote_knowledge",
                    HumanApproval.action_payload.contains(str(version_id)),
                )
            ).all()
            session.execute(
                delete(AuditEvent).where(
                    (AuditEvent.resource_id == str(version_id))
                    | (AuditEvent.resource_id.in_([str(item) for item in approval_ids]))
                    | (AuditEvent.actor_id.in_([admin_id, supervisor_id]))
                )
            )
            session.execute(
                delete(KnowledgeVersion).where(KnowledgeVersion.id == version_id)
            )
            if approval_ids:
                session.execute(
                    delete(HumanApproval).where(HumanApproval.id.in_(approval_ids))
                )
            session.execute(
                delete(KnowledgeDocument).where(KnowledgeDocument.id == document_id)
            )
            session.execute(delete(User).where(User.id.in_([admin_id, supervisor_id])))
