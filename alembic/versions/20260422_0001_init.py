"""initial schema

Revision ID: 20260422_0001
Revises: None
Create Date: 2026-04-22
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260422_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=True),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False, server_default="operator"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "missions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("drone_id", sa.String(length=64), nullable=True),
        sa.Column("waypoints", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_missions_status", "missions", ["status"])
    op.create_index("ix_missions_priority", "missions", ["priority"])
    op.create_index("ix_missions_drone_id", "missions", ["drone_id"])
    op.create_index("ix_missions_created_by_user_id", "missions", ["created_by_user_id"])

    op.create_table(
        "scan_results",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("mission_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("drone_id", sa.String(length=64), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("evidence_object_key", sa.String(length=1024), nullable=True),
        sa.ForeignKeyConstraint(["mission_id"], ["missions.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_scan_results_mission_id", "scan_results", ["mission_id"])
    op.create_index("ix_scan_results_drone_id", "scan_results", ["drone_id"])

    op.create_table(
        "report_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("report_type", sa.String(length=64), nullable=False),
        sa.Column("params", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("created_by_user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("result_object_key", sa.String(length=1024), nullable=True),
        sa.Column("error_message", sa.String(length=1024), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_report_jobs_report_type", "report_jobs", ["report_type"])
    op.create_index("ix_report_jobs_status", "report_jobs", ["status"])
    op.create_index("ix_report_jobs_created_by_user_id", "report_jobs", ["created_by_user_id"])


def downgrade() -> None:
    op.drop_index("ix_report_jobs_created_by_user_id", table_name="report_jobs")
    op.drop_index("ix_report_jobs_status", table_name="report_jobs")
    op.drop_index("ix_report_jobs_report_type", table_name="report_jobs")
    op.drop_table("report_jobs")

    op.drop_index("ix_scan_results_drone_id", table_name="scan_results")
    op.drop_index("ix_scan_results_mission_id", table_name="scan_results")
    op.drop_table("scan_results")

    op.drop_index("ix_missions_created_by_user_id", table_name="missions")
    op.drop_index("ix_missions_drone_id", table_name="missions")
    op.drop_index("ix_missions_priority", table_name="missions")
    op.drop_index("ix_missions_status", table_name="missions")
    op.drop_table("missions")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

