from __future__ import annotations

import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role
from app.core.config import settings
from app.core.rbac import Role
from app.db.session import AsyncSessionLocal, get_session
from app.repositories.report_jobs import ReportJobsRepository
from app.schemas.report import PresignDownloadResponse, ReportJobCreate, ReportJobOut
from app.services.report_service import ReportService
from app.services.s3_service import S3Service

router = APIRouter()


async def _run_report_job(job_id: uuid.UUID) -> None:
    async with AsyncSessionLocal() as session:
        await ReportService(session).run_job_inline(job_id)


@router.post("", response_model=ReportJobOut, status_code=status.HTTP_202_ACCEPTED)
async def create_report_job(
    payload: ReportJobCreate,
    user=Depends(require_role(Role.supervisor)),
    session: AsyncSession = Depends(get_session),
) -> ReportJobOut:
    job = await ReportJobsRepository(session).create(
        report_type=payload.report_type, params=payload.params, created_by_user_id=user.id
    )
    await session.commit()

    # Hook: enqueue work.
    # - Inline mode: run inside the API process for simplicity (dev default).
    # - Worker mode: leave job "queued"; ai-worker will pick it up.
    if settings.REPORT_JOBS_INLINE:
        asyncio.create_task(_run_report_job(job.id))
    return ReportJobOut.model_validate(job)


@router.get("", response_model=list[ReportJobOut])
async def list_report_jobs(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user=Depends(require_role(Role.supervisor)),
    session: AsyncSession = Depends(get_session),
) -> list[ReportJobOut]:
    jobs = await ReportJobsRepository(session).list(created_by_user_id=user.id, limit=limit, offset=offset)
    return [ReportJobOut.model_validate(j) for j in jobs]


@router.get("/{job_id}", response_model=ReportJobOut)
async def get_report_job(
    job_id: uuid.UUID,
    user=Depends(require_role(Role.supervisor)),
    session: AsyncSession = Depends(get_session),
) -> ReportJobOut:
    job = await ReportJobsRepository(session).get(job_id)
    if not job or job.created_by_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report job not found")
    return ReportJobOut.model_validate(job)


@router.get("/{job_id}/download", response_model=PresignDownloadResponse)
async def download_report_job(
    job_id: uuid.UUID,
    user=Depends(require_role(Role.supervisor)),
    session: AsyncSession = Depends(get_session),
) -> PresignDownloadResponse:
    """
    Return a pre-signed GET URL for the report job output.

    Dashboard uses this to trigger downloads without proxying S3 content.
    """
    job = await ReportJobsRepository(session).get(job_id)
    if not job or job.created_by_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report job not found")
    if not job.result_object_key:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Report is not ready")

    url = S3Service().presign_get_url(object_key=job.result_object_key)
    return PresignDownloadResponse(url=url, expires_in_seconds=settings.S3_PRESIGN_EXPIRES_SECONDS)

