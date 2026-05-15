from __future__ import annotations

import asyncio
import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.rbac import Role, role_at_least
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.db.session import get_session
from app.repositories.missions import MissionsRepository
from app.repositories.scan_jobs import ScanJobsRepository
from app.repositories.scan_results import ScanResultsRepository
from app.schemas.upload import ConfirmUploadRequest, ConfirmUploadResponse, PresignUploadRequest, PresignUploadResponse
from app.services.scan_job_service import ScanJobService
from app.services.s3_service import S3Service

router = APIRouter()


async def _run_scan_job(job_id: uuid.UUID) -> None:
    async with AsyncSessionLocal() as session:
        await ScanJobService(session).run_job_inline(job_id)


@router.post("/presign", response_model=PresignUploadResponse)
async def presign_upload(
    payload: PresignUploadRequest,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PresignUploadResponse:
    scan = await ScanResultsRepository(session).get(payload.scan_result_id)
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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to upload evidence")

    content_type = payload.content_type.split(";", 1)[0].strip().lower()
    if content_type not in {"image/jpeg", "image/png", "application/octet-stream"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported content_type")

    existing = scan.evidence_object_key
    if existing:
        object_key = existing.lstrip("/")
    else:
        filename = (payload.filename or "evidence").strip()
        filename = re.sub(r"[^A-Za-z0-9._-]+", "_", filename)[:100].strip("._-") or "evidence"
        ext = ".jpg" if content_type == "image/jpeg" else ".png" if content_type == "image/png" else ""
        object_key = f"evidence/scan-results/{scan.id}/{uuid.uuid4().hex}-{filename}{ext}"
        scan.evidence_object_key = object_key
        await session.commit()

    url = S3Service().presign_put_url(object_key=object_key, content_type=content_type)
    return PresignUploadResponse(
        method="PUT",
        url=url,
        headers={"Content-Type": content_type},
        expires_in_seconds=settings.S3_PRESIGN_EXPIRES_SECONDS,
        object_key=object_key,
    )


@router.post("/confirm", response_model=ConfirmUploadResponse)
async def confirm_upload(
    payload: ConfirmUploadRequest,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ConfirmUploadResponse:
    scan = await ScanResultsRepository(session).get(payload.scan_result_id)
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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to upload evidence")

    object_key = (scan.evidence_object_key or "").lstrip("/")
    if not object_key:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Scan result has no evidence object")

    meta = await S3Service().head_object_async(object_key=object_key)
    if not meta:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Evidence object not found")

    etag: str | None = meta.get("etag") if isinstance(meta, dict) else None
    size: int | None = meta.get("bytes") if isinstance(meta, dict) else None
    stored_content_type: str | None = meta.get("content_type") if isinstance(meta, dict) else None

    if stored_content_type and stored_content_type.lower() not in {"image/jpeg", "image/png", "application/octet-stream"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported evidence Content-Type in storage")

    if payload.etag and etag and payload.etag.strip().strip('"') != etag:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ETag mismatch")
    if payload.bytes is not None and size is not None and payload.bytes != size:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Size mismatch")

    scan.evidence_etag = etag or (payload.etag.strip().strip('"') if payload.etag else None)
    scan.evidence_bytes = size or payload.bytes
    scan.evidence_uploaded_at = datetime.now(timezone.utc)
    await session.commit()

    scan_job_id: uuid.UUID | None = None
    if settings.SCAN_JOBS_AUTO_ENQUEUE:
        job = await ScanJobsRepository(session).create_or_get(scan_result_id=scan.id)
        await session.commit()
        scan_job_id = job.id
        if settings.SCAN_JOBS_INLINE:
            asyncio.create_task(_run_scan_job(job.id))

    return ConfirmUploadResponse(
        scan_result_id=scan.id,
        object_key=object_key,
        etag=scan.evidence_etag,
        bytes=scan.evidence_bytes,
        uploaded_at=scan.evidence_uploaded_at,
        scan_job_id=scan_job_id,
    )

