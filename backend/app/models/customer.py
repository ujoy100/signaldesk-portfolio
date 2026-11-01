from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base


class Customer(Base):
    """Telecom customer record."""

    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)

    customer_number: Mapped[str] = mapped_column(
        String(30), unique=True, nullable=False
    )

    full_name: Mapped[str] = mapped_column(String(150), nullable=False)

    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
