"""scan_results created_by_user_id

Revision ID: 20260423_0003
Revises: 20260422_0002
Create Date: 2026-04-23
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260423_0003"
down_revision = "20260422_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("scan_results", sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_scan_results_created_by_user_id", "scan_results", ["created_by_user_id"])
    op.create_foreign_key(
        "fk_scan_results_created_by_user_id_users",
        "scan_results",
        "users",
        ["created_by_user_id"],
        ["id"],
        ondelete="RESTRICT",
    )

    op.execute(
        """
        UPDATE scan_results sr
        SET created_by_user_id = m.created_by_user_id
        FROM missions m
        WHERE sr.mission_id = m.id
          AND sr.created_by_user_id IS NULL
        """
    )

    op.alter_column("scan_results", "created_by_user_id", existing_type=postgresql.UUID(as_uuid=True), nullable=False)


def downgrade() -> None:
    op.drop_constraint("fk_scan_results_created_by_user_id_users", "scan_results", type_="foreignkey")
    op.drop_index("ix_scan_results_created_by_user_id", table_name="scan_results")
    op.drop_column("scan_results", "created_by_user_id")
