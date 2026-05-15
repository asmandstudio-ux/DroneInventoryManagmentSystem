"""warehouses + risk events + barcodes + scan jobs

Revision ID: 20260422_0002
Revises: 20260422_0001
Create Date: 2026-04-22
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260422_0002"
down_revision = "20260422_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "warehouses",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("code", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("code", name="uq_warehouses_code"),
    )
    op.create_index("ix_warehouses_code", "warehouses", ["code"], unique=True)

    op.create_table(
        "risk_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("mission_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scan_result_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("drone_id", sa.String(length=64), nullable=True),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["mission_id"], ["missions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["scan_result_id"], ["scan_results.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_risk_events_mission_id", "risk_events", ["mission_id"])
    op.create_index("ix_risk_events_scan_result_id", "risk_events", ["scan_result_id"])
    op.create_index("ix_risk_events_drone_id", "risk_events", ["drone_id"])
    op.create_index("ix_risk_events_severity", "risk_events", ["severity"])
    op.create_index("ix_risk_events_category", "risk_events", ["category"])

    op.create_table(
        "barcode_reads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scan_result_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("symbology", sa.String(length=32), nullable=False),
        sa.Column("value", sa.String(length=512), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("meta", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["scan_result_id"], ["scan_results.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("scan_result_id", "symbology", "value", name="uq_barcode_reads_scan_sym_value"),
    )
    op.create_index("ix_barcode_reads_scan_result_id", "barcode_reads", ["scan_result_id"])
    op.create_index("ix_barcode_reads_symbology", "barcode_reads", ["symbology"])
    op.create_index("ix_barcode_reads_value", "barcode_reads", ["value"])

    op.create_table(
        "scan_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("scan_result_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("result", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("error_message", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["scan_result_id"], ["scan_results.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("scan_result_id", name="uq_scan_jobs_scan_result_id"),
    )
    op.create_index("ix_scan_jobs_scan_result_id", "scan_jobs", ["scan_result_id"], unique=True)
    op.create_index("ix_scan_jobs_status", "scan_jobs", ["status"])


def downgrade() -> None:
    op.drop_index("ix_scan_jobs_status", table_name="scan_jobs")
    op.drop_index("ix_scan_jobs_scan_result_id", table_name="scan_jobs")
    op.drop_table("scan_jobs")

    op.drop_index("ix_barcode_reads_value", table_name="barcode_reads")
    op.drop_index("ix_barcode_reads_symbology", table_name="barcode_reads")
    op.drop_index("ix_barcode_reads_scan_result_id", table_name="barcode_reads")
    op.drop_table("barcode_reads")

    op.drop_index("ix_risk_events_category", table_name="risk_events")
    op.drop_index("ix_risk_events_severity", table_name="risk_events")
    op.drop_index("ix_risk_events_drone_id", table_name="risk_events")
    op.drop_index("ix_risk_events_scan_result_id", table_name="risk_events")
    op.drop_index("ix_risk_events_mission_id", table_name="risk_events")
    op.drop_table("risk_events")

    op.drop_index("ix_warehouses_code", table_name="warehouses")
    op.drop_table("warehouses")

