from __future__ import annotations

import uuid

from sqlalchemy import Select, delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.warehouse import Warehouse


class WarehousesRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, warehouse_id: uuid.UUID) -> Warehouse | None:
        return await self.session.get(Warehouse, warehouse_id)

    async def get_by_code(self, code: str) -> Warehouse | None:
        stmt: Select[tuple[Warehouse]] = select(Warehouse).where(Warehouse.code == code)
        return (await self.session.scalars(stmt)).first()

    async def list(self, *, limit: int = 100, offset: int = 0) -> list[Warehouse]:
        stmt: Select[tuple[Warehouse]] = select(Warehouse).order_by(Warehouse.code.asc()).limit(limit).offset(offset)
        return list(await self.session.scalars(stmt))

    async def create(self, *, code: str, name: str, address: str | None, metadata: dict) -> Warehouse:
        wh = Warehouse(code=code, name=name, address=address, meta=metadata)
        self.session.add(wh)
        await self.session.flush()
        return wh

    async def patch(
        self,
        warehouse: Warehouse,
        *,
        code: str | None = None,
        name: str | None = None,
        address: str | None = None,
        metadata: dict | None = None,
    ) -> Warehouse:
        if code is not None:
            warehouse.code = code
        if name is not None:
            warehouse.name = name
        if address is not None:
            warehouse.address = address
        if metadata is not None:
            warehouse.meta = metadata
        await self.session.flush()
        return warehouse

    async def delete(self, warehouse_id: uuid.UUID) -> None:
        await self.session.execute(delete(Warehouse).where(Warehouse.id == warehouse_id))
