from __future__ import annotations

import asyncio
import os

from sqlalchemy import select

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.report_job import ReportJob, ReportJobStatus
from app.models.scan_job import ScanJob, ScanJobStatus
from app.services.report_service import ReportService
from app.services.scan_job_service import ScanJobService


POLL_SECONDS = float(os.getenv("WORKER_POLL_SECONDS", "1.0"))


async def _claim_one_queued_job(session) -> ReportJob | None:
    """
    Claim a single queued job using row-level locking (safe for multiple workers).
    """
    stmt = (
        select(ReportJob)
        .where(ReportJob.status == ReportJobStatus.queued.value)
        .order_by(ReportJob.created_at.asc())
        .with_for_update(skip_locked=True)
        .limit(1)
    )

    job = (await session.scalars(stmt)).first()
    if not job:
        return None

    job.status = ReportJobStatus.running.value
    await session.commit()
    return job


async def _claim_one_queued_scan_job(session) -> ScanJob | None:
    stmt = (
        select(ScanJob)
        .where(ScanJob.status == ScanJobStatus.queued.value)
        .order_by(ScanJob.created_at.asc())
        .with_for_update(skip_locked=True)
        .limit(1)
    )

    job = (await session.scalars(stmt)).first()
    if not job:
        return None

    job.status = ScanJobStatus.running.value
    await session.commit()
    return job


async def run_forever() -> None:
    """
    Minimal local-dev worker that drains queued report jobs from Postgres.

    Production: replace with Redis/RabbitMQ/SQS + proper worker framework.
    """
    if settings.REPORT_JOBS_INLINE or settings.SCAN_JOBS_INLINE:
        raise RuntimeError(
            "Inline jobs enabled; worker would conflict with inline execution. "
            "Set REPORT_JOBS_INLINE=false and SCAN_JOBS_INLINE=false to use the worker."
        )

    while True:
        async with AsyncSessionLocal() as session:
            report_job = await _claim_one_queued_job(session)
            scan_job = await _claim_one_queued_scan_job(session)

            if not report_job and not scan_job:
                await asyncio.sleep(POLL_SECONDS)
                continue

            # Process in a fresh session to keep transactions short and predictable.
            report_job_id = report_job.id if report_job else None
            scan_job_id = scan_job.id if scan_job else None

        async with AsyncSessionLocal() as session:
            if report_job_id:
                await ReportService(session).run_job_inline(report_job_id)
            if scan_job_id:
                await ScanJobService(session).run_job_inline(scan_job_id)


def main() -> None:
    asyncio.run(run_forever())


if __name__ == "__main__":
    main()
