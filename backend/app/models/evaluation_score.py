from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class EvaluationScore(Base):
    """A quality metric recorded for an evaluation run."""

    __tablename__ = "evaluation_scores"

    id: Mapped[int] = mapped_column(primary_key=True)

    evaluation_run_id: Mapped[int] = mapped_column(
        ForeignKey("evaluation_runs.id"),
        nullable=False,
    )

    metric_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    details: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "score >= 0 AND score <= 1",
            name="ck_evaluation_scores_range",
        ),
        Index(
            "ix_evaluation_scores_evaluation_run_id",
            "evaluation_run_id",
        ),
        Index(
            "ix_evaluation_scores_metric_name",
            "metric_name",
        ),
    )
