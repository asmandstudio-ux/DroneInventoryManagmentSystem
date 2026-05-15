from __future__ import annotations

import uuid

from sqlalchemy import Select, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.warehouse_map import WarehouseMap


class WarehouseMapsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, warehouse_map_id: uuid.UUID) -> WarehouseMap | None:
        return await self.session.get(WarehouseMap, warehouse_map_id)

    async def get_in_warehouse(self, *, warehouse_id: uuid.UUID, warehouse_map_id: uuid.UUID) -> WarehouseMap | None:
        stmt: Select[tuple[WarehouseMap]] = select(WarehouseMap).where(
            WarehouseMap.id == warehouse_map_id, WarehouseMap.warehouse_id == warehouse_id
        )
        return (await self.session.scalars(stmt)).first()

    async def list_by_warehouse(
        self,
        *,
        warehouse_id: uuid.UUID,
        limit: int = 100,
        offset: int = 0,
        created_by_user_id: uuid.UUID | None = None,
    ) -> list[WarehouseMap]:
        stmt: Select[tuple[WarehouseMap]] = (
            select(WarehouseMap)
            .where(WarehouseMap.warehouse_id == warehouse_id)
            .order_by(WarehouseMap.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if created_by_user_id is not None:
            stmt = stmt.where(WarehouseMap.created_by_user_id == created_by_user_id)
        return list(await self.session.scalars(stmt))

    async def create(
        self,
        *,
        warehouse_id: uuid.UUID,
        created_by_user_id: uuid.UUID,
        name: str,
        locations: dict,
    ) -> WarehouseMap:
        wm = WarehouseMap(
            warehouse_id=warehouse_id,
            created_by_user_id=created_by_user_id,
            name=name,
            locations=locations,
            mesh_object_key=None,
        )
        self.session.add(wm)
        await self.session.flush()
        return wm

    async def patch(self, warehouse_map: WarehouseMap, *, name: str | None = None, locations: dict | None = None) -> WarehouseMap:
        if name is not None:
            warehouse_map.name = name
        if locations is not None:
            warehouse_map.locations = locations
        await self.session.flush()
        return warehouse_map

    async def delete(self, *, warehouse_map_id: uuid.UUID) -> None:
        await self.session.execute(delete(WarehouseMap).where(WarehouseMap.id == warehouse_map_id))

