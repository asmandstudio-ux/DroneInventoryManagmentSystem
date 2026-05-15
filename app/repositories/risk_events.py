from __future__ import annotations

import uuid

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.risk_event import RiskEvent


class RiskEventsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, risk_event_id: uuid.UUID) -> RiskEvent | None:
        return await self.session.get(RiskEvent, risk_event_id)

    async def create(
        self,
        *,
        mission_id: uuid.UUID | None,
        scan_result_id: uuid.UUID | None,
        drone_id: str | None,
        severity: str,
        category: str,
        message: str,
        details: dict,
    ) -> RiskEvent:
        ev = RiskEvent(
            mission_id=mission_id,
            scan_result_id=scan_result_id,
            drone_id=drone_id,
            severity=severity,
            category=category,
            message=message,
            details=details,
        )
        self.session.add(ev)
        await self.session.flush()
        return ev

    async def list(
        self,
        *,
        mission_id: uuid.UUID | None = None,
        scan_result_id: uuid.UUID | None = None,
        drone_id: str | None = None,
        severity: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[RiskEvent]:
        stmt: Select[tuple[RiskEvent]] = select(RiskEvent).order_by(RiskEvent.created_at.desc())
        if mission_id is not None:
            stmt = stmt.where(RiskEvent.mission_id == mission_id)
        if scan_result_id is not None:
            stmt = stmt.where(RiskEvent.scan_result_id == scan_result_id)
        if drone_id is not None:
            stmt = stmt.where(RiskEvent.drone_id == drone_id)
        if severity is not None:
            stmt = stmt.where(RiskEvent.severity == severity)
        stmt = stmt.limit(limit).offset(offset)
        return list(await self.session.scalars(stmt))

