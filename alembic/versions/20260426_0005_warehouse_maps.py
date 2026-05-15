"""warehouse_maps

Revision ID: 20260426_0005
Revises: 20260423_0004
Create Date: 2026-04-26
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260426_0005"
down_revision = "20260423_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "warehouse_maps",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "warehouse_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("warehouses.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "created_by_user_id",
            sa.dialects.postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("locations", sa.dialects.postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("mesh_object_key", sa.Text(), nullable=True),
        sa.Column("mesh_etag", sa.String(length=128), nullable=True),
        sa.Column("mesh_bytes", sa.BigInteger(), nullable=True),
        sa.Column("mesh_uploaded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_warehouse_maps_warehouse_id", "warehouse_maps", ["warehouse_id"])
    op.create_index("ix_warehouse_maps_created_by_user_id", "warehouse_maps", ["created_by_user_id"])


def downgrade() -> None:
    op.drop_index("ix_warehouse_maps_created_by_user_id", table_name="warehouse_maps")
    op.drop_index("ix_warehouse_maps_warehouse_id", table_name="warehouse_maps")
    op.drop_table("warehouse_maps")

