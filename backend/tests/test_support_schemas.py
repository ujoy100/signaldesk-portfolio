"""Strict Phase 8 structured-output tests."""

import pytest
from pydantic import ValidationError

from backend.app.schemas.support import SupportResolution, TicketDraft


def test_valid_insufficient_evidence_resolution() -> None:
    result = SupportResolution(
        issue_type="unknown",
        likely_cause="Insufficient evidence",
        evidence=[],
        confidence=0.0,
        next_steps=["Escalate"],
        action_required=False,
        requires_human_approval=False,
        insufficient_evidence=True,
    )
    assert result.insufficient_evidence


@pytest.mark.parametrize(
    "changes",
    [
        {"confidence": 1.1},
        {"action_required": True, "requires_human_approval": False},
        {
            "action_required": False,
            "ticket_draft": TicketDraft(
                operation="update_ticket", payload={"ticket_id": 1}
            ),
        },
        {"confidence": 0.5, "insufficient_evidence": True},
    ],
)
def test_resolution_rejects_malformed_or_contradictory_data(changes: dict) -> None:
    values = {
        "issue_type": "general",
        "likely_cause": "cause",
        "evidence": [],
        "confidence": 0.5,
        "next_steps": [],
        "action_required": False,
        "requires_human_approval": False,
        "insufficient_evidence": False,
    }
    values.update(changes)
    with pytest.raises(ValidationError):
        SupportResolution(**values)


def test_resolution_forbids_unexpected_fields() -> None:
    with pytest.raises(ValidationError):
        SupportResolution.model_validate({"unexpected": True})
