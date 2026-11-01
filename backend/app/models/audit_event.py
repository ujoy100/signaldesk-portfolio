from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class AuditEvent(Base):
    """Security and operational audit event."""

    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(primary_key=True)

    actor_type: Mapped[str] = mapped_column(String(30), nullable=False)

    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    action: Mapped[str] = mapped_column(String(100), nullable=False)

    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)

    resource_id: Mapped[str | None] = mapped_column(String(100), nullable=True)

    outcome: Mapped[str] = mapped_column(String(30), nullable=False)

    details: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index("ix_audit_events_actor_id", "actor_id"),
        Index("ix_audit_events_created_at", "created_at"),
        Index("ix_audit_events_action", "action"),
    )
