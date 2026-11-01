from datetime import datetime

from sqlalchemy import (
    JSON,
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


class KnowledgeVersion(Base):
    """Immutable uploaded content and mutable promotion lifecycle state."""

    __tablename__ = "knowledge_versions"

    id: Mapped[int] = mapped_column(primary_key=True)
    document_id: Mapped[int] = mapped_column(
        ForeignKey("knowledge_documents.id"), nullable=False
    )
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), server_default="draft", nullable=False
    )
    supersedes_id: Mapped[int | None] = mapped_column(
        ForeignKey("knowledge_versions.id"), nullable=True
    )
    approval_id: Mapped[int | None] = mapped_column(
        ForeignKey("human_approvals.id"), nullable=True
    )
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    promoted_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    promoted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    promotion_state: Mapped[str] = mapped_column(
        String(20), nullable=False, default="none", server_default="none"
    )
    promotion_request_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    qdrant_point_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    promotion_error: Mapped[str | None] = mapped_column(String(200), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'active', 'inactive', 'rejected')",
            name="ck_knowledge_versions_status",
        ),
        CheckConstraint(
            "promotion_state IN ('none', 'staging', 'staged', 'committed', 'published')",
            name="ck_knowledge_versions_promotion_state",
        ),
        UniqueConstraint(
            "document_id", "version", name="uq_knowledge_versions_document_version"
        ),
        UniqueConstraint(
            "document_id", "checksum", name="uq_knowledge_versions_document_checksum"
        ),
        Index("ix_knowledge_versions_document_id", "document_id"),
        Index("ix_knowledge_versions_status", "status"),
        UniqueConstraint(
            "promotion_request_id",
            name="uq_knowledge_versions_promotion_request_id",
        ),
    )
