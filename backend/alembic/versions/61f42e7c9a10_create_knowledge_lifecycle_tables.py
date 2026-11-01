"""create knowledge lifecycle tables

Revision ID: 61f42e7c9a10
Revises: 926cf9047962
Create Date: 2026-10-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "61f42e7c9a10"
down_revision: str | Sequence[str] | None = "926cf9047962"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("stable_id", sa.String(length=36), nullable=False),
        sa.Column("source", sa.String(length=500), nullable=False),
        sa.Column("title", sa.String(length=250), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stable_id"),
    )
    op.create_index("ix_knowledge_documents_source", "knowledge_documents", ["source"])
    op.create_table(
        "knowledge_versions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("version", sa.String(length=50), nullable=False),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=False),
        sa.Column(
            "status", sa.String(length=20), server_default="draft", nullable=False
        ),
        sa.Column("supersedes_id", sa.Integer(), nullable=True),
        sa.Column("approval_id", sa.Integer(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("promoted_by", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("promoted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "status IN ('draft', 'active', 'inactive', 'rejected')",
            name="ck_knowledge_versions_status",
        ),
        sa.ForeignKeyConstraint(["approval_id"], ["human_approvals.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["document_id"], ["knowledge_documents.id"]),
        sa.ForeignKeyConstraint(["promoted_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["supersedes_id"], ["knowledge_versions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "document_id", "checksum", name="uq_knowledge_versions_document_checksum"
        ),
        sa.UniqueConstraint(
            "document_id", "version", name="uq_knowledge_versions_document_version"
        ),
    )
    op.create_index(
        "ix_knowledge_versions_document_id", "knowledge_versions", ["document_id"]
    )
    op.create_index("ix_knowledge_versions_status", "knowledge_versions", ["status"])


def downgrade() -> None:
    op.drop_index("ix_knowledge_versions_status", table_name="knowledge_versions")
    op.drop_index("ix_knowledge_versions_document_id", table_name="knowledge_versions")
    op.drop_table("knowledge_versions")
    op.drop_index("ix_knowledge_documents_source", table_name="knowledge_documents")
    op.drop_table("knowledge_documents")
