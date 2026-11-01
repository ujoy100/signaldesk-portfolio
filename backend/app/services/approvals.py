"""Transactional approval lifecycle and exact-scope verification."""

import hashlib
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.audit_event import AuditEvent
from backend.app.models.human_approval import HumanApproval
from backend.app.models.role import Role
from backend.app.models.user import User
from backend.app.schemas.support import ApprovalDecisionRequest, TicketDraft

DECISION_ROLES = {"supervisor", "admin"}


class ApprovalError(PermissionError):
    pass


def canonical_action(operation: str, payload: dict) -> tuple[str, str]:
    encoded = json.dumps(
        {"operation": operation, "payload": payload},
        sort_keys=True,
        separators=(",", ":"),
    )
    return encoded, hashlib.sha256(encoded.encode()).hexdigest()


class ApprovalService:
    def __init__(self, session: Session) -> None:
        self.session = session

    def request(
        self, *, thread_id: str, draft: TicketDraft, ticket_id: int | None
    ) -> HumanApproval:
        return self.request_action(
            thread_id=thread_id,
            operation=draft.operation,
            payload=draft.payload,
            ticket_id=ticket_id,
        )

    def request_action(
        self,
        *,
        thread_id: str,
        operation: str,
        payload: dict,
        ticket_id: int | None = None,
    ) -> HumanApproval:
        """Create an approval for any registered controlled action."""

        encoded, digest = canonical_action(operation, payload)
        approval = HumanApproval(
            ticket_id=ticket_id,
            action_type=operation,
            action_description=f"Controlled {operation}",
            thread_id=thread_id,
            request_id=str(uuid4()),
            action_payload=encoded,
            action_digest=digest,
            expires_at=datetime.now(UTC) + timedelta(hours=24),
        )
        self.session.add(approval)
        self.session.flush()
        self._audit(approval, None, "approval_requested", "pending")
        return approval

    def decide(
        self, approval_id: int, decision: ApprovalDecisionRequest, actor_id: int
    ) -> HumanApproval:
        approval = self.session.scalar(
            select(HumanApproval)
            .where(HumanApproval.id == approval_id)
            .with_for_update()
        )
        if approval is None or approval.status != "pending" or approval.consumed:
            raise ApprovalError("approval is not pending")
        role = self.session.scalar(
            select(Role.name)
            .join(User, User.role_id == Role.id)
            .where(User.id == actor_id, User.is_active.is_(True))
        )
        if role not in DECISION_ROLES:
            raise ApprovalError("supervisor or admin role required")
        now = datetime.now(UTC)
        if approval.expires_at is not None and approval.expires_at <= now:
            approval.status = "expired"
            self._audit(approval, actor_id, "approval_expired", "denied")
            raise ApprovalError("approval has expired")
        approval.reviewer_id = actor_id
        approval.reviewed_at = now
        approval.decision_note = decision.note
        if decision.decision == "reject":
            approval.status = "rejected"
        elif decision.decision == "edit":
            # A material edit invalidates the original scope. The API creates a
            # separate pending request for the new canonical action.
            approval.status = "rejected"
        else:
            approval.status = "approved"
        self._audit(
            approval, actor_id, f"approval_{decision.decision}", approval.status
        )
        return approval

    def verify(
        self,
        *,
        approval_id: int,
        operation: str,
        payload: dict,
        execution_request_id: str,
    ) -> HumanApproval:
        approval = self.session.scalar(
            select(HumanApproval)
            .where(HumanApproval.id == approval_id)
            .with_for_update()
        )
        _, digest = canonical_action(operation, payload)
        now = datetime.now(UTC)
        if approval is None:
            raise ApprovalError("approval not found")
        if approval.status != "approved" or approval.consumed:
            raise ApprovalError("approval is not executable")
        if approval.expires_at is not None and approval.expires_at <= now:
            approval.status = "expired"
            raise ApprovalError("approval has expired")
        if approval.action_type != operation or approval.action_digest != digest:
            raise ApprovalError("approval scope mismatch")
        if approval.execution_request_id not in (None, execution_request_id):
            raise ApprovalError("approval replay detected")
        return approval

    def consume(self, approval: HumanApproval, execution_request_id: str) -> None:
        approval.consumed = True
        approval.executed_at = datetime.now(UTC)
        approval.execution_request_id = execution_request_id
        self._audit(approval, approval.reviewer_id, "approval_executed", "allowed")

    def _audit(
        self, approval: HumanApproval, actor_id: int | None, action: str, outcome: str
    ) -> None:
        self.session.add(
            AuditEvent(
                actor_type="user" if actor_id else "workflow",
                actor_id=actor_id,
                action=action,
                resource_type="human_approval",
                resource_id=str(approval.id),
                outcome=outcome,
                details=json.dumps(
                    {
                        "thread_id": approval.thread_id,
                        "action_digest": approval.action_digest,
                    },
                    sort_keys=True,
                ),
            )
        )
