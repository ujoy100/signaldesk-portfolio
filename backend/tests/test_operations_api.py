from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from backend.app.api.routes.operations import (
    list_approvals,
    list_evaluations,
    list_knowledge_versions,
    session_info,
)


class FakeSession:
    def __init__(self, rows):
        self.rows = rows

    def scalars(self, _statement):
        return SimpleNamespace(all=lambda: self.rows)

    def get(self, _model, identifier):
        if identifier is None:
            return None
        return SimpleNamespace(
            ticket_number="FIC-TKT-004", status="open", priority="high"
        )


def test_session_contract_and_role_denials() -> None:
    request = SimpleNamespace(
        state=SimpleNamespace(auth_display_name="Verified Microsoft User")
    )
    assert session_info(request, (7, "support_agent")).model_dump() == {
        "actor_id": 7,
        "role": "support_agent",
        "display_name": "Verified Microsoft User",
    }
    with pytest.raises(HTTPException, match="Supervisor or admin"):
        list_approvals((7, "support_agent"), FakeSession([]))
    with pytest.raises(HTTPException, match="Admin role"):
        list_knowledge_versions((7, "supervisor"), FakeSession([]))


def test_operational_views_serialize_persisted_records() -> None:
    approvals = list_approvals(
        (2, "supervisor"),
        FakeSession(
            [
                SimpleNamespace(
                    id=3,
                    thread_id="thread-123",
                    status="approved",
                    action_type="update_ticket",
                    action_payload='{"payload":{"ticket_id":4}}',
                    consumed=True,
                    action_description="Update fictional ticket",
                    expires_at=None,
                    ticket_id=4,
                )
            ]
        ),
    )
    assert approvals[0].status == "executed"
    assert approvals[0].action_payload == {"ticket_id": 4}
    assert approvals[0].ticket_number == "FIC-TKT-004"
    assert approvals[0].current_ticket_status == "open"

    evaluations = list_evaluations(
        (2, "supervisor"),
        FakeSession(
            [
                SimpleNamespace(
                    id=5,
                    evaluation_type="deterministic_offline",
                    dataset_name="fictional-v1",
                    model_name=None,
                    status="passed",
                    configuration="{}",
                )
            ]
        ),
    )
    assert evaluations[0].evaluation_type == "deterministic_offline"

    versions = list_knowledge_versions(
        (1, "admin"),
        FakeSession(
            [
                SimpleNamespace(
                    id=8,
                    document_id=9,
                    version="2",
                    status="draft",
                    promotion_state="staged",
                    promotion_error=None,
                )
            ]
        ),
    )
    assert versions[0].promotion_state == "staged"
