"""add verified display name to browser sessions

Revision ID: 2d4f8a71c930
Revises: 8b6f2d91a4ce
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "2d4f8a71c930"
down_revision: str | Sequence[str] | None = "8b6f2d91a4ce"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "auth_sessions",
        sa.Column(
            "display_name",
            sa.String(length=150),
            server_default="Microsoft user",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("auth_sessions", "display_name")
