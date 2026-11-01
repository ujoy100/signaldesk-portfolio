"""extend approvals for phase 9

Revision ID: a6d9c8421b7e
Revises: 61f42e7c9a10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "a6d9c8421b7e"
down_revision: str | Sequence[str] | None = "61f42e7c9a10"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("human_approvals", sa.Column("thread_id", sa.String(100)))
    op.add_column("human_approvals", sa.Column("request_id", sa.String(100)))
    op.add_column("human_approvals", sa.Column("action_payload", sa.Text()))
    op.add_column("human_approvals", sa.Column("action_digest", sa.String(64)))
    op.add_column("human_approvals", sa.Column("decision_note", sa.Text()))
    op.add_column(
        "human_approvals", sa.Column("expires_at", sa.DateTime(timezone=True))
    )
    op.add_column(
        "human_approvals", sa.Column("executed_at", sa.DateTime(timezone=True))
    )
    op.add_column("human_approvals", sa.Column("execution_request_id", sa.String(100)))
    op.add_column(
        "human_approvals",
        sa.Column("consumed", sa.Boolean(), server_default=sa.false(), nullable=False),
    )
    # Existing Phase 1 rows remain present but cannot pass Phase 9 verification.
    op.execute("UPDATE human_approvals SET thread_id = 'legacy-' || id::text")
    op.execute("UPDATE human_approvals SET request_id = 'legacy-' || id::text")
    op.execute("UPDATE human_approvals SET action_payload = '{}'")
    op.execute("UPDATE human_approvals SET action_digest = repeat('0', 64)")
    op.alter_column("human_approvals", "thread_id", nullable=False)
    op.alter_column("human_approvals", "request_id", nullable=False)
    op.alter_column("human_approvals", "action_payload", nullable=False)
    op.alter_column("human_approvals", "action_digest", nullable=False)
    op.create_index("ix_human_approvals_thread_id", "human_approvals", ["thread_id"])
    op.create_unique_constraint(
        "uq_human_approvals_request_id", "human_approvals", ["request_id"]
    )
    op.create_unique_constraint(
        "uq_human_approvals_execution_request_id",
        "human_approvals",
        ["execution_request_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_human_approvals_execution_request_id", "human_approvals", type_="unique"
    )
    op.drop_constraint(
        "uq_human_approvals_request_id", "human_approvals", type_="unique"
    )
    op.drop_index("ix_human_approvals_thread_id", table_name="human_approvals")
    for column in (
        "consumed",
        "execution_request_id",
        "executed_at",
        "expires_at",
        "decision_note",
        "action_digest",
        "action_payload",
        "request_id",
        "thread_id",
    ):
        op.drop_column("human_approvals", column)
