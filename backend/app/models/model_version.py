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


class ModelVersion(Base):
    """Versioned AI model configuration."""

    __tablename__ = "model_versions"

    id: Mapped[int] = mapped_column(primary_key=True)

    model_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    provider: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    model_identifier: Mapped[str] = mapped_column(
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
            "model_name",
            "version",
            name="uq_model_versions_name_version",
        ),
        Index(
            "ix_model_versions_model_name",
            "model_name",
        ),
    )
