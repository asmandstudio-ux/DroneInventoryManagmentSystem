from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scan_job import ScanJobStatus
from app.repositories.scan_jobs import ScanJobsRepository
from app.services.barcode_service import BarcodeService


class ScanJobService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.jobs = ScanJobsRepository(session)
        self.barcodes = BarcodeService(session)

    async def run_job_inline(self, job_id: uuid.UUID) -> None:
        job = await self.jobs.get(job_id)
        if not job:
            return

        job.status = ScanJobStatus.running.value
        await self.session.commit()

        try:
            res = await self.barcodes.process_scan_result(job.scan_result_id)
            job.result = {**(job.result or {}), "processing": res}

            if res.get("ok") is True:
                job.status = ScanJobStatus.completed.value
                job.error_message = None
            else:
                job.status = ScanJobStatus.failed.value
                job.error_message = str(res.get("error") or "scan_job_failed")[:1024]
        except Exception as exc:  # noqa: BLE001
            job.status = ScanJobStatus.failed.value
            job.error_message = str(exc)[:1024]

        await self.session.commit()
