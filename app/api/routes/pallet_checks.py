from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_session
from app.models.pallet_check import PalletCheck, PalletReview
from app.models.user import User
from app.repositories.pallet_checks import PalletChecksRepository
from app.schemas.pallet_check import (
    PalletCheckOut,
    PalletCheckSummary,
    PalletReviewCreate,
    PalletReviewOut,
)
from app.services.pallet_safety_service import PalletModelUnavailable, pallet_safety_service

router = APIRouter()


@router.get("/status")
async def pallet_model_status(_: User = Depends(get_current_user)) -> dict:
    """Whether the pallet-safety model is loaded (and, if not, why)."""
    return pallet_safety_service.status()


@router.post("")
async def create_pallet_check(
    file: UploadFile = File(...),
    pallet_mm: float | None = Form(None),
    reference: str = Form("auto"),
    warehouse_id: uuid.UUID | None = Form(None),
    location_code: str | None = Form(None),
    store: bool = Form(True),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Upload one warehouse photo and get the pallet lean / stack safety result — the same JSON
    the web tool and the ``pallet_safety`` CLI produce (``overall``, per-pallet ``verdict``,
    ``outsideMm``, lean angle, stacks, ...), returned under ``result``.

    ``pallet_mm`` overrides the pallet width facing the camera (default 1200 mm Euro).
    ``reference`` is ``auto`` (rack uprights, else the photo vertical), ``photo``, or a number
    of degrees. When ``store`` is true (default) the result is saved and its ``check_id`` is
    returned. Returns 503 if the model (or onnxruntime) is not deployed.
    """
    data = await file.read()
    if not data:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="empty upload")
    limits = {"pallet_mm": pallet_mm} if pallet_mm is not None else None
    try:
        result = await run_in_threadpool(
            pallet_safety_service.analyse, data, limits=limits, reference=reference
        )
    except PalletModelUnavailable as exc:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc))

    response: dict = {"result": result}
    if store:
        check = await PalletChecksRepository(session).create(
            created_by_user_id=user.id,
            warehouse_id=warehouse_id,
            location_code=location_code,
            overall=result.get("overall"),
            model_version=pallet_safety_service.model_version,
            result=result,
        )
        await session.commit()
        response["check_id"] = str(check.id)
    return response


@router.get("", response_model=list[PalletCheckSummary])
async def list_pallet_checks(
    warehouse_id: uuid.UUID | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[PalletCheck]:
    """List the current user's pallet checks (newest first), optionally filtered by warehouse."""
    return await PalletChecksRepository(session).list_for_user(
        user_id=user.id, warehouse_id=warehouse_id, limit=limit, offset=offset
    )


@router.get("/{check_id}", response_model=PalletCheckOut)
async def get_pallet_check(
    check_id: uuid.UUID,
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PalletCheck:
    """Fetch one stored pallet check, including its full result."""
    check = await PalletChecksRepository(session).get(check_id)
    if not check:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Pallet check not found")
    return check


@router.post("/{check_id}/reviews", response_model=PalletReviewOut, status_code=status.HTTP_201_CREATED)
async def add_pallet_review(
    check_id: uuid.UUID,
    body: PalletReviewCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PalletReview:
    """Record a reviewer correction for a pallet (or the whole photo) — feeds model retraining."""
    repo = PalletChecksRepository(session)
    if not await repo.get(check_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Pallet check not found")
    review = await repo.add_review(
        check_id=check_id,
        reviewer_user_id=user.id,
        pallet_id=body.pallet_id,
        call=body.call,
        lines=body.lines,
    )
    await session.commit()
    return review


@router.get("/{check_id}/reviews", response_model=list[PalletReviewOut])
async def list_pallet_reviews(
    check_id: uuid.UUID,
    _: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[PalletReview]:
    """List the reviewer corrections recorded for a pallet check."""
    return await PalletChecksRepository(session).list_reviews(check_id=check_id)
