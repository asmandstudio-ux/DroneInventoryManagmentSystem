from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ScanResult(Base):
    __tablename__ = "scan_results"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    mission_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    drone_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Flexible data: barcodes, detected SKUs, counts, confidence, etc.
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Optional link to uploaded evidence (image/video) in S3 (object key)
    evidence_object_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    evidence_etag: Mapped[str | None] = mapped_column(String(128), nullable=True)
    evidence_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    evidence_uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

