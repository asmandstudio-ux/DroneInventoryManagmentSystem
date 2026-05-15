from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mission import Mission, MissionStatus


class MissionsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, mission_id: uuid.UUID) -> Mission | None:
        return await self.session.get(Mission, mission_id)

    async def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        status: str | None = None,
        created_by_user_id: uuid.UUID | None = None,
    ) -> list[Mission]:
        stmt: Select[tuple[Mission]] = select(Mission).order_by(Mission.created_at.desc()).limit(limit).offset(offset)
        if status:
            stmt = stmt.where(Mission.status == status)
        if created_by_user_id:
            stmt = stmt.where(Mission.created_by_user_id == created_by_user_id)
        rows = await self.session.scalars(stmt)
        return list(rows)

    async def create(
        self,
        *,
        title: str,
        description: str | None,
        priority: int,
        drone_id: str | None,
        waypoints: dict,
        created_by_user_id: uuid.UUID,
    ) -> Mission:
        mission = Mission(
            title=title,
            description=description,
            priority=priority,
            drone_id=drone_id,
            waypoints=waypoints,
            status=MissionStatus.queued.value,
            created_by_user_id=created_by_user_id,
        )
        self.session.add(mission)
        await self.session.flush()
        return mission

    async def patch(
        self,
        mission: Mission,
        *,
        title: str | None = None,
        description: str | None = None,
        priority: int | None = None,
        drone_id: str | None = None,
        waypoints: dict | None = None,
    ) -> Mission:
        if title is not None:
            mission.title = title
        if description is not None:
            mission.description = description
        if priority is not None:
            mission.priority = priority
        if drone_id is not None:
            mission.drone_id = drone_id
        if waypoints is not None:
            mission.waypoints = waypoints
        await self.session.flush()
        return mission

    async def set_status(self, mission: Mission, status: MissionStatus) -> Mission:
        mission.status = status.value
        now = datetime.now(timezone.utc)
        if status in {MissionStatus.launching, MissionStatus.in_flight} and mission.started_at is None:
            mission.started_at = now
        if status in {MissionStatus.completed, MissionStatus.aborted, MissionStatus.failed} and mission.completed_at is None:
            mission.completed_at = now
        await self.session.flush()
        return mission

