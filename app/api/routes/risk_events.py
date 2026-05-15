from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import require_role
from app.core.rbac import Role
from app.db.session import get_session
from app.repositories.risk_events import RiskEventsRepository
from app.schemas.risk_event import RiskEventCreate, RiskEventOut

router = APIRouter()


@router.post("", response_model=RiskEventOut, status_code=status.HTTP_201_CREATED)
async def create_risk_event(
    payload: RiskEventCreate,
    _user=Depends(require_role(Role.supervisor)),
    session: AsyncSession = Depends(get_session),
) -> RiskEventOut:
    ev = await RiskEventsRepository(session).create(
        mission_id=payload.mission_id,
        scan_result_id=payload.scan_result_id,
        drone_id=payload.drone_id,
        severity=payload.severity.value,
        category=payload.category,
        message=payload.message,
        details=payload.details,
    )
    await session.commit()
    return RiskEventOut.model_validate(ev)


@router.get("", response_model=list[RiskEventOut])
async def list_risk_events(
    mission_id: uuid.UUID | None = Query(default=None),
    scan_result_id: uuid.UUID | None = Query(default=None),
    drone_id: str | None = Query(default=None),
    severity: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _user=Depends(require_role(Role.supervisor)),
    session: AsyncSession = Depends(get_session),
) -> list[RiskEventOut]:
    events = await RiskEventsRepository(session).list(
        mission_id=mission_id,
        scan_result_id=scan_result_id,
        drone_id=drone_id,
        severity=severity,
        limit=limit,
        offset=offset,
    )
    return [RiskEventOut.model_validate(e) for e in events]


@router.get("/{risk_event_id}", response_model=RiskEventOut)
async def get_risk_event(
    risk_event_id: uuid.UUID,
    _user=Depends(require_role(Role.supervisor)),
    session: AsyncSession = Depends(get_session),
) -> RiskEventOut:
    ev = await RiskEventsRepository(session).get(risk_event_id)
    if not ev:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk event not found")
    return RiskEventOut.model_validate(ev)

