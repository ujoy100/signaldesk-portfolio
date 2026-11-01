"""add recoverable knowledge promotion state

Revision ID: c3e7a91d5f20
Revises: a6d9c8421b7e
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c3e7a91d5f20"
down_revision: str | Sequence[str] | None = "a6d9c8421b7e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "knowledge_versions",
        sa.Column(
            "promotion_state", sa.String(20), server_default="none", nullable=False
        ),
    )
    op.add_column(
        "knowledge_versions", sa.Column("promotion_request_id", sa.String(100))
    )
    op.add_column("knowledge_versions", sa.Column("qdrant_point_id", sa.String(36)))
    op.add_column("knowledge_versions", sa.Column("promotion_error", sa.String(200)))
    op.create_check_constraint(
        "ck_knowledge_versions_promotion_state",
        "knowledge_versions",
        "promotion_state IN ('none', 'staging', 'staged', 'committed', 'published')",
    )
    op.create_unique_constraint(
        "uq_knowledge_versions_promotion_request_id",
        "knowledge_versions",
        ["promotion_request_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_knowledge_versions_promotion_request_id",
        "knowledge_versions",
        type_="unique",
    )
    op.drop_constraint(
        "ck_knowledge_versions_promotion_state", "knowledge_versions", type_="check"
    )
    op.drop_column("knowledge_versions", "promotion_error")
    op.drop_column("knowledge_versions", "qdrant_point_id")
    op.drop_column("knowledge_versions", "promotion_request_id")
    op.drop_column("knowledge_versions", "promotion_state")
