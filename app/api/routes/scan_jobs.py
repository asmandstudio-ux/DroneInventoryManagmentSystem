from __future__ import annotations

import asyncio
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.api.deps import get_current_user
from app.core.rbac import Role, role_at_least
from app.db.session import AsyncSessionLocal, get_session
from app.repositories.missions import MissionsRepository
from app.repositories.scan_jobs import ScanJobsRepository
from app.repositories.scan_results import ScanResultsRepository
from app.services.scan_job_service import ScanJobService
from app.schemas.scan_job import ScanJobCreate, ScanJobOut

router = APIRouter()


async def _run_scan_job(job_id: uuid.UUID) -> None:
    async with AsyncSessionLocal() as session:
        await ScanJobService(session).run_job_inline(job_id)


async def _require_scan_result_access(*, scan_result_id: uuid.UUID, user, session: AsyncSession):
    scan = await ScanResultsRepository(session).get(scan_result_id)
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan result not found")
    mission = await MissionsRepository(session).get(scan.mission_id)
    if not mission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")
    try:
        user_role = Role(user.role)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid user role")
    if not role_at_least(user_role, Role.supervisor) and mission.created_by_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    return scan


async def _require_scan_job_access(*, scan_job_id: uuid.UUID, user, session: AsyncSession):
    job = await ScanJobsRepository(session).get(scan_job_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan job not found")
    await _require_scan_result_access(scan_result_id=job.scan_result_id, user=user, session=session)
    return job


@router.post("", response_model=ScanJobOut, status_code=status.HTTP_202_ACCEPTED)
async def enqueue_scan_job(
    payload: ScanJobCreate,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ScanJobOut:
    await _require_scan_result_access(scan_result_id=payload.scan_result_id, user=user, session=session)

    # Create (idempotent per scan_result_id)
    repo = ScanJobsRepository(session)
    job = await repo.create_or_get(scan_result_id=payload.scan_result_id)
    await session.commit()

    if settings.SCAN_JOBS_INLINE:
        asyncio.create_task(_run_scan_job(job.id))

    return ScanJobOut.model_validate(job)


@router.get("", response_model=list[ScanJobOut])
async def list_scan_jobs(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[ScanJobOut]:
    try:
        user_role = Role(user.role)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid user role")
    repo = ScanJobsRepository(session)
    if role_at_least(user_role, Role.supervisor):
        jobs = await repo.list(limit=limit, offset=offset)
    else:
        jobs = await repo.list_for_user(user_id=user.id, limit=limit, offset=offset)
    return [ScanJobOut.model_validate(j) for j in jobs]


@router.get("/{scan_job_id}", response_model=ScanJobOut)
async def get_scan_job(
    scan_job_id: uuid.UUID,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ScanJobOut:
    job = await _require_scan_job_access(scan_job_id=scan_job_id, user=user, session=session)
    return ScanJobOut.model_validate(job)
