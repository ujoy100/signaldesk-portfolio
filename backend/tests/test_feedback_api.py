"""Authenticated feedback API integration tests."""

from collections.abc import Iterator
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import Connection
from sqlalchemy.orm import Session, sessionmaker

from backend.app.api.routes.support import get_support_db, get_verified_actor
from backend.app.core.config import Settings
from backend.app.main import create_app


def test_feedback_submission_history_and_scope(
    test_db_connection: Connection,
) -> None:
    factory = sessionmaker(
        bind=test_db_connection,
        join_transaction_mode="create_savepoint",
        expire_on_commit=False,
    )
    session = factory()

    def override_db() -> Iterator[Session]:
        yield session

    app = create_app(Settings(_env_file=None, app_env="testing"))
    app.dependency_overrides[get_support_db] = override_db
    app.dependency_overrides[get_verified_actor] = lambda: (10, "support_agent")
    client = TestClient(app)
    thread_id = f"feedback-{uuid4()}"

    created = client.post(
        "/api/v1/feedback",
        json={
            "thread_id": thread_id,
            "rating": 5,
            "comment": "The fictional activation guidance was useful.",
        },
    )
    denied = client.get("/api/v1/feedback")

    assert created.status_code == 201, created.text
    assert created.json()["thread_id"] == thread_id
    assert denied.status_code == 403

    app.dependency_overrides[get_verified_actor] = lambda: (11, "supervisor")
    history = client.get("/api/v1/feedback")
    assert history.status_code == 200, history.text
    assert any(item["thread_id"] == thread_id for item in history.json())

    mismatch = client.post(
        "/api/v1/feedback",
        json={"thread_id": thread_id, "customer_id": 999999, "rating": 3},
    )
    assert mismatch.status_code in {409, 422}
    session.close()
