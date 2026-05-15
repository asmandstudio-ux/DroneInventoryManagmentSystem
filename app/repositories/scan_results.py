from __future__ import annotations

import uuid

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scan_result import ScanResult


class ScanResultsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, scan_result_id: uuid.UUID) -> ScanResult | None:
        return await self.session.get(ScanResult, scan_result_id)

    async def list_by_mission(self, *, mission_id: uuid.UUID, limit: int = 100, offset: int = 0) -> list[ScanResult]:
        stmt: Select[tuple[ScanResult]] = (
            select(ScanResult)
            .where(ScanResult.mission_id == mission_id)
            .order_by(ScanResult.captured_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = await self.session.scalars(stmt)
        return list(rows)

    async def create(
        self,
        *,
        mission_id: uuid.UUID,
        created_by_user_id: uuid.UUID,
        drone_id: str | None,
        data: dict,
        evidence_object_key: str | None,
    ) -> ScanResult:
        scan = ScanResult(
            mission_id=mission_id,
            created_by_user_id=created_by_user_id,
            drone_id=drone_id,
            data=data,
            evidence_object_key=evidence_object_key,
        )
        self.session.add(scan)
        await self.session.flush()
        return scan

