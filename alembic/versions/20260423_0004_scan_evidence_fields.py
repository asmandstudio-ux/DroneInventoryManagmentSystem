"""scan_results evidence fields

Revision ID: 20260423_0004
Revises: 20260423_0003
Create Date: 2026-04-23
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "20260423_0004"
down_revision = "20260423_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("scan_results", sa.Column("evidence_etag", sa.String(length=128), nullable=True))
    op.add_column("scan_results", sa.Column("evidence_bytes", sa.BigInteger(), nullable=True))
    op.add_column("scan_results", sa.Column("evidence_uploaded_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("scan_results", "evidence_uploaded_at")
    op.drop_column("scan_results", "evidence_bytes")
    op.drop_column("scan_results", "evidence_etag")

