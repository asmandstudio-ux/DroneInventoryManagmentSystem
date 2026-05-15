from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.rbac import Role, role_at_least
from app.repositories.missions import MissionsRepository
from app.repositories.barcode_reads import BarcodeReadsRepository
from app.repositories.scan_jobs import ScanJobsRepository
from app.repositories.scan_results import ScanResultsRepository
from app.schemas.barcode import BarcodeDecodeRequest, BarcodeReadOut
from app.schemas.report import PresignDownloadResponse
from app.schemas.scan_job import ScanJobOut
from app.schemas.scan_result import ScanResultCreate, ScanResultOut
from app.db.session import get_session
from app.db.session import AsyncSessionLocal
from app.services.s3_service import S3Service
from app.services.scan_job_service import ScanJobService

router = APIRouter()


async def _run_scan_job(job_id: uuid.UUID) -> None:
    async with AsyncSessionLocal() as session:
        await ScanJobService(session).run_job_inline(job_id)


async def _require_scan_access(
    *,
    scan_result_id: uuid.UUID,
    user,
    session: AsyncSession,
):
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


@router.post("", response_model=ScanResultOut, status_code=status.HTTP_201_CREATED)
async def create_scan_result(
    payload: ScanResultCreate,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ScanResultOut:
    # Validate mission exists
    mission = await MissionsRepository(session).get(payload.mission_id)
    if not mission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")
    try:
        user_role = Role(user.role)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid user role")
    if not role_at_least(user_role, Role.supervisor) and mission.created_by_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to create scan results")

    scan = await ScanResultsRepository(session).create(
        mission_id=payload.mission_id,
        created_by_user_id=user.id,
        drone_id=payload.drone_id,
        data=payload.data,
        evidence_object_key=None,
    )
    await session.commit()
    return ScanResultOut.model_validate(scan)


@router.get("", response_model=list[ScanResultOut])
async def list_scan_results(
    mission_id: uuid.UUID = Query(...),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[ScanResultOut]:
    mission = await MissionsRepository(session).get(mission_id)
    if not mission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")
    try:
        user_role = Role(user.role)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid user role")
    if not role_at_least(user_role, Role.supervisor) and mission.created_by_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    scans = await ScanResultsRepository(session).list_by_mission(mission_id=mission_id, limit=limit, offset=offset)
    return [ScanResultOut.model_validate(s) for s in scans]


@router.get("/{scan_result_id}", response_model=ScanResultOut)
async def get_scan_result(
    scan_result_id: uuid.UUID,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ScanResultOut:
    scan = await _require_scan_access(scan_result_id=scan_result_id, user=user, session=session)
    return ScanResultOut.model_validate(scan)


@router.get("/{scan_result_id}/evidence/download", response_model=PresignDownloadResponse)
async def download_scan_evidence(
    scan_result_id: uuid.UUID,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PresignDownloadResponse:
    scan = await _require_scan_access(scan_result_id=scan_result_id, user=user, session=session)
    if not scan.evidence_object_key:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Scan result has no evidence object")
    url = S3Service().presign_get_url(object_key=scan.evidence_object_key)
    return PresignDownloadResponse(url=url, expires_in_seconds=settings.S3_PRESIGN_EXPIRES_SECONDS)


@router.get("/{scan_result_id}/barcodes", response_model=list[BarcodeReadOut])
async def list_scan_barcodes(
    scan_result_id: uuid.UUID,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[BarcodeReadOut]:
    await _require_scan_access(scan_result_id=scan_result_id, user=user, session=session)
    reads = await BarcodeReadsRepository(session).list_by_scan_result(scan_result_id=scan_result_id)
    return [BarcodeReadOut.model_validate(r) for r in reads]


@router.post("/{scan_result_id}/process", response_model=ScanJobOut, status_code=status.HTTP_202_ACCEPTED)
async def enqueue_scan_processing(
    scan_result_id: uuid.UUID,
    payload: BarcodeDecodeRequest,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ScanJobOut:
    await _require_scan_access(scan_result_id=scan_result_id, user=user, session=session)
    job = await ScanJobsRepository(session).create_or_get(scan_result_id=scan_result_id)
    await session.commit()
    if settings.SCAN_JOBS_INLINE:
        import asyncio

        asyncio.create_task(_run_scan_job(job.id))
    return ScanJobOut.model_validate(job)

