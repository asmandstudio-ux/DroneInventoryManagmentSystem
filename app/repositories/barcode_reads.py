from __future__ import annotations

import uuid

from sqlalchemy import Select, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.barcode_read import BarcodeRead


class BarcodeReadsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_scan_result(self, *, scan_result_id: uuid.UUID) -> list[BarcodeRead]:
        stmt: Select[tuple[BarcodeRead]] = (
            select(BarcodeRead)
            .where(BarcodeRead.scan_result_id == scan_result_id)
            .order_by(BarcodeRead.created_at.desc())
        )
        return list(await self.session.scalars(stmt))

    async def upsert_many(self, *, scan_result_id: uuid.UUID, barcodes: list[dict]) -> None:
        """
        Upsert by (scan_result_id, symbology, value).
        """
        if not barcodes:
            return

        rows = []
        for b in barcodes:
            rows.append(
                {
                    "scan_result_id": scan_result_id,
                    "symbology": str(b.get("symbology") or "UNKNOWN"),
                    "value": str(b.get("value") or ""),
                    "confidence": float(b.get("confidence") or 1.0),
                    "meta": dict(b.get("meta") or {}),
                }
            )

        stmt = insert(BarcodeRead).values(rows)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_barcode_reads_scan_sym_value",
            set_={
                "confidence": stmt.excluded.confidence,
                "meta": stmt.excluded.meta,
            },
        )
        await self.session.execute(stmt)

