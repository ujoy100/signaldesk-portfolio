from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class HumanApproval(Base):
    """Human approval request for a proposed AI agent action."""

    __tablename__ = "human_approvals"

    id: Mapped[int] = mapped_column(primary_key=True)

    ticket_id: Mapped[int | None] = mapped_column(
        ForeignKey("tickets.id"),
        nullable=True,
    )

    action_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    action_description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        server_default="pending",
        nullable=False,
    )

    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    reviewer_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )
    thread_id: Mapped[str] = mapped_column(
        String(100), nullable=False, default=lambda: f"legacy-{uuid4()}"
    )
    request_id: Mapped[str] = mapped_column(
        String(100), nullable=False, default=lambda: str(uuid4())
    )
    action_payload: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    action_digest: Mapped[str] = mapped_column(
        String(64), nullable=False, default="legacy"
    )
    decision_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    execution_request_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    consumed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'expired')",
            name="ck_human_approvals_status",
        ),
        Index("ix_human_approvals_status", "status"),
        Index("ix_human_approvals_ticket_id", "ticket_id"),
        Index("ix_human_approvals_thread_id", "thread_id"),
        UniqueConstraint("request_id", name="uq_human_approvals_request_id"),
        UniqueConstraint(
            "execution_request_id", name="uq_human_approvals_execution_request_id"
        ),
    )
