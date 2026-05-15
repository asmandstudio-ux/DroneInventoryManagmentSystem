from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, require_role
from app.core.rbac import Role
from app.db.session import get_session
from app.repositories.warehouses import WarehousesRepository
from app.schemas.warehouse import WarehouseCreate, WarehouseOut, WarehouseUpdate

router = APIRouter()


@router.post("", response_model=WarehouseOut, status_code=status.HTTP_201_CREATED)
async def create_warehouse(
    payload: WarehouseCreate,
    _user=Depends(require_role(Role.supervisor)),
    session: AsyncSession = Depends(get_session),
) -> WarehouseOut:
    repo = WarehousesRepository(session)
    try:
        wh = await repo.create(code=payload.code, name=payload.name, address=payload.address, metadata=payload.metadata)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Warehouse code already exists")
    return WarehouseOut.model_validate(wh)


@router.get("", response_model=list[WarehouseOut])
async def list_warehouses(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    _user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[WarehouseOut]:
    whs = await WarehousesRepository(session).list(limit=limit, offset=offset)
    return [WarehouseOut.model_validate(w) for w in whs]


@router.get("/{warehouse_id}", response_model=WarehouseOut)
async def get_warehouse(
    warehouse_id: uuid.UUID,
    _user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> WarehouseOut:
    wh = await WarehousesRepository(session).get(warehouse_id)
    if not wh:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")
    return WarehouseOut.model_validate(wh)


@router.patch("/{warehouse_id}", response_model=WarehouseOut)
async def update_warehouse(
    warehouse_id: uuid.UUID,
    payload: WarehouseUpdate,
    _user=Depends(require_role(Role.supervisor)),
    session: AsyncSession = Depends(get_session),
) -> WarehouseOut:
    repo = WarehousesRepository(session)
    wh = await repo.get(warehouse_id)
    if not wh:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")

    try:
        wh = await repo.patch(wh, code=payload.code, name=payload.name, address=payload.address, metadata=payload.metadata)
        await session.commit()
    except IntegrityError:
        await session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Warehouse code already exists")

    return WarehouseOut.model_validate(wh)


@router.delete("/{warehouse_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_warehouse(
    warehouse_id: uuid.UUID,
    _user=Depends(require_role(Role.supervisor)),
    session: AsyncSession = Depends(get_session),
) -> None:
    repo = WarehousesRepository(session)
    wh = await repo.get(warehouse_id)
    if not wh:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")
    await repo.delete(warehouse_id)
    await session.commit()
    return None

