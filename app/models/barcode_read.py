from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class BarcodeRead(Base):
    __tablename__ = "barcode_reads"
    __table_args__ = (
        UniqueConstraint("scan_result_id", "symbology", "value", name="uq_barcode_reads_scan_sym_value"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    scan_result_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scan_results.id", ondelete="CASCADE"), nullable=False, index=True
    )

    symbology: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    value: Mapped[str] = mapped_column(String(512), nullable=False, index=True)
    confidence: Mapped[float] = mapped_column(nullable=False, default=1.0)

    # Optional decoded bbox/meta (xyxy, preprocessing variant, rotation, etc.)
    meta: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

