from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.core.rbac import Role
from app.core.rbac import role_at_least
from app.models.mission import MissionStatus
from app.repositories.missions import MissionsRepository
from app.schemas.mission import MissionCreate, MissionOut, MissionStatusUpdate, MissionUpdate
from app.db.session import get_session

router = APIRouter()


@router.post("", response_model=MissionOut, status_code=status.HTTP_201_CREATED)
async def create_mission(
    payload: MissionCreate,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MissionOut:
    mission = await MissionsRepository(session).create(
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        drone_id=payload.drone_id,
        waypoints=payload.waypoints,
        created_by_user_id=user.id,
    )
    await session.commit()
    return MissionOut.model_validate(mission)


@router.get("", response_model=list[MissionOut])
async def list_missions(
    status_: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[MissionOut]:
    try:
        user_role = Role(user.role)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid user role")
    created_by_user_id = None if role_at_least(user_role, Role.supervisor) else user.id
    missions = await MissionsRepository(session).list(
        limit=limit,
        offset=offset,
        status=status_,
        created_by_user_id=created_by_user_id,
    )
    return [MissionOut.model_validate(m) for m in missions]


@router.get("/{mission_id}", response_model=MissionOut)
async def get_mission(
    mission_id: uuid.UUID,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MissionOut:
    mission = await MissionsRepository(session).get(mission_id)
    if not mission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")
    try:
        user_role = Role(user.role)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid user role")
    if not role_at_least(user_role, Role.supervisor) and mission.created_by_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    return MissionOut.model_validate(mission)


@router.patch("/{mission_id}", response_model=MissionOut)
async def update_mission(
    mission_id: uuid.UUID,
    payload: MissionUpdate,
    _user=Depends(require_role(Role.supervisor)),
    session: AsyncSession = Depends(get_session),
) -> MissionOut:
    repo = MissionsRepository(session)
    mission = await repo.get(mission_id)
    if not mission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")
    mission = await repo.patch(
        mission,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        drone_id=payload.drone_id,
        waypoints=payload.waypoints,
    )
    await session.commit()
    return MissionOut.model_validate(mission)


@router.post("/{mission_id}/status", response_model=MissionOut)
async def set_mission_status(
    mission_id: uuid.UUID,
    payload: MissionStatusUpdate,
    _user=Depends(require_role(Role.supervisor)),
    session: AsyncSession = Depends(get_session),
) -> MissionOut:
    repo = MissionsRepository(session)
    mission = await repo.get(mission_id)
    if not mission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")
    mission = await repo.set_status(mission, payload.status)
    await session.commit()
    return MissionOut.model_validate(mission)


@router.post("/{mission_id}/abort", response_model=MissionOut)
async def abort_mission(
    mission_id: uuid.UUID,
    _user=Depends(require_role(Role.supervisor)),
    session: AsyncSession = Depends(get_session),
) -> MissionOut:
    repo = MissionsRepository(session)
    mission = await repo.get(mission_id)
    if not mission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found")
    mission = await repo.set_status(mission, MissionStatus.aborted)
    await session.commit()
    return MissionOut.model_validate(mission)

