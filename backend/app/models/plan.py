from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class Plan(Base):
    """Telecom mobile service plan."""

    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(primary_key=True)

    plan_code: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)

    name: Mapped[str] = mapped_column(String(100), nullable=False)

    plan_type: Mapped[str] = mapped_column(String(20), nullable=False)

    monthly_price: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)

    data_allowance_gb: Mapped[int] = mapped_column(nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
