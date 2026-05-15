from __future__ import annotations

import uuid

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.report_job import ReportJob


class ReportJobsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, job_id: uuid.UUID) -> ReportJob | None:
        return await self.session.get(ReportJob, job_id)

    async def list(self, *, created_by_user_id: uuid.UUID, limit: int = 50, offset: int = 0) -> list[ReportJob]:
        stmt: Select[tuple[ReportJob]] = (
            select(ReportJob)
            .where(ReportJob.created_by_user_id == created_by_user_id)
            .order_by(ReportJob.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        rows = await self.session.scalars(stmt)
        return list(rows)

    async def create(self, *, report_type: str, params: dict, created_by_user_id: uuid.UUID) -> ReportJob:
        job = ReportJob(report_type=report_type, params=params, created_by_user_id=created_by_user_id)
        self.session.add(job)
        await self.session.flush()
        return job

