from __future__ import annotations

import uuid

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mission import Mission
from app.models.scan_job import ScanJob, ScanJobStatus
from app.models.scan_result import ScanResult


class ScanJobsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, scan_job_id: uuid.UUID) -> ScanJob | None:
        return await self.session.get(ScanJob, scan_job_id)

    async def get_by_scan_result(self, scan_result_id: uuid.UUID) -> ScanJob | None:
        stmt: Select[tuple[ScanJob]] = select(ScanJob).where(ScanJob.scan_result_id == scan_result_id)
        return (await self.session.scalars(stmt)).first()

    async def create_or_get(self, *, scan_result_id: uuid.UUID) -> ScanJob:
        job = await self.get_by_scan_result(scan_result_id)
        if job:
            return job

        job = ScanJob(
            scan_result_id=scan_result_id,
            status=ScanJobStatus.queued.value,
            result={},
        )
        self.session.add(job)
        await self.session.flush()
        return job

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[ScanJob]:
        stmt: Select[tuple[ScanJob]] = select(ScanJob).order_by(ScanJob.created_at.desc()).limit(limit).offset(offset)
        return list(await self.session.scalars(stmt))

    async def list_for_user(self, *, user_id: uuid.UUID, limit: int = 100, offset: int = 0) -> list[ScanJob]:
        stmt: Select[tuple[ScanJob]] = (
            select(ScanJob)
            .join(ScanResult, ScanJob.scan_result_id == ScanResult.id)
            .join(Mission, ScanResult.mission_id == Mission.id)
            .where(Mission.created_by_user_id == user_id)
            .order_by(ScanJob.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(await self.session.scalars(stmt))
