from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PalletCheck(Base):
    """One pallet-safety analysis of a warehouse photo (the full ``analyse_image`` result)."""

    __tablename__ = "pallet_checks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    warehouse_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=True, index=True
    )

    # Rack address the photo was taken at (e.g. "A-04-L3"), when known.
    location_code: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)

    # Worst verdict across the photo: ok | check | unsafe | no_pallets.
    overall: Mapped[str | None] = mapped_column(String(16), nullable=True, index=True)

    # Which detector produced this (the model file stem), for the retraining loop.
    model_version: Mapped[str | None] = mapped_column(String(64), nullable=True)

    # Full analyse_image() output (pallets, stacks, reference, limits, ...).
    result: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    # Optional link to the uploaded photo in S3 (object key).
    evidence_object_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    reviews: Mapped[list["PalletReview"]] = relationship(
        back_populates="check", cascade="all, delete-orphan"
    )


class PalletReview(Base):
    """A reviewer correction to one pallet (or stack) in a :class:`PalletCheck` — feeds retraining."""

    __tablename__ = "pallet_reviews"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    check_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("pallet_checks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewer_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    # Which pallet in the result (its "id", e.g. "p4"); null for a whole-photo / stack note.
    pallet_id: Mapped[str | None] = mapped_column(String(16), nullable=True)

    # Reviewer ground truth: "straight" | "leaning" | "not_pallet" | a verdict override.
    call: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Corrected geometry (same shape as the result's pallet "lines"), optional.
    lines: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    check: Mapped["PalletCheck"] = relationship(back_populates="reviews")
