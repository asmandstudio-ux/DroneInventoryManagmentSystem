"""pallet_checks

Revision ID: 20261108_0006
Revises: 20260426_0005
Create Date: 2026-11-08
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20261108_0006"
down_revision = "20260426_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pallet_checks",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "created_by_user_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "warehouse_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("warehouses.id", ondelete="CASCADE"),
            nullable=True,
        ),
        sa.Column("location_code", sa.String(length=64), nullable=True),
        sa.Column("overall", sa.String(length=16), nullable=True),
        sa.Column("model_version", sa.String(length=64), nullable=True),
        sa.Column("result", sa.dialects.postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence_object_key", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_pallet_checks_created_by_user_id", "pallet_checks", ["created_by_user_id"])
    op.create_index("ix_pallet_checks_warehouse_id", "pallet_checks", ["warehouse_id"])
    op.create_index("ix_pallet_checks_location_code", "pallet_checks", ["location_code"])
    op.create_index("ix_pallet_checks_overall", "pallet_checks", ["overall"])

    op.create_table(
        "pallet_reviews",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "check_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("pallet_checks.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "reviewer_user_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("pallet_id", sa.String(length=16), nullable=True),
        sa.Column("call", sa.String(length=32), nullable=True),
        sa.Column("lines", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_pallet_reviews_check_id", "pallet_reviews", ["check_id"])
    op.create_index("ix_pallet_reviews_reviewer_user_id", "pallet_reviews", ["reviewer_user_id"])


def downgrade() -> None:
    op.drop_index("ix_pallet_reviews_reviewer_user_id", table_name="pallet_reviews")
    op.drop_index("ix_pallet_reviews_check_id", table_name="pallet_reviews")
    op.drop_table("pallet_reviews")
    op.drop_index("ix_pallet_checks_overall", table_name="pallet_checks")
    op.drop_index("ix_pallet_checks_location_code", table_name="pallet_checks")
    op.drop_index("ix_pallet_checks_warehouse_id", table_name="pallet_checks")
    op.drop_index("ix_pallet_checks_created_by_user_id", table_name="pallet_checks")
    op.drop_table("pallet_checks")
