from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class RetrieverVersion(Base):
    """Versioned configuration for the RAG retrieval pipeline."""

    __tablename__ = "retriever_versions"

    id: Mapped[int] = mapped_column(primary_key=True)

    retriever_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    retrieval_strategy: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    collection_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    embedding_model: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    configuration: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        server_default="false",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "retriever_name",
            "version",
            name="uq_retriever_versions_name_version",
        ),
        Index(
            "ix_retriever_versions_retriever_name",
            "retriever_name",
        ),
    )
