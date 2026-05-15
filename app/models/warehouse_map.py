from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WarehouseMap(Base):
    """
    Warehouse mapping artifacts.

    - `locations` holds warehouse-specific POIs / anchors / named coordinates used by
      mission planning (loading zones, charging docks, pallet bays, etc.).
    - `mesh_object_key` points to the uploaded mesh stored in S3 (glb/gltf/etc).
    """

    __tablename__ = "warehouse_maps"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    warehouse_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("warehouses.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    locations: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    mesh_object_key: Mapped[str | None] = mapped_column(Text(), nullable=True)
    mesh_etag: Mapped[str | None] = mapped_column(String(128), nullable=True)
    mesh_bytes: Mapped[int | None] = mapped_column(BigInteger(), nullable=True)
    mesh_uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

