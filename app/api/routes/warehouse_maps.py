from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.rbac import Role, role_at_least
from app.db.session import get_session
from app.repositories.warehouse_maps import WarehouseMapsRepository
from app.repositories.warehouses import WarehousesRepository
from app.schemas.warehouse_map import (
    ConfirmWarehouseMapMeshRequest,
    ConfirmWarehouseMapMeshResponse,
    PresignWarehouseMapMeshRequest,
    PresignWarehouseMapMeshResponse,
    WarehouseMapMeshDownloadResponse,
    WarehouseMapCreate,
    WarehouseMapOut,
    WarehouseMapUpdate,
)
from app.services.s3_service import S3Service

router = APIRouter()


ALLOWED_MESH_CONTENT_TYPES: set[str] = {
    "model/gltf-binary",
    "model/gltf+json",
    "application/octet-stream",
}


def _parse_role(user) -> Role:
    try:
        return Role(user.role)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid user role")


async def _require_warehouse(*, warehouse_id: uuid.UUID, session: AsyncSession):
    wh = await WarehousesRepository(session).get(warehouse_id)
    if not wh:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse not found")
    return wh


async def _require_map_access(
    *,
    warehouse_id: uuid.UUID,
    warehouse_map_id: uuid.UUID,
    user,
    session: AsyncSession,
    write: bool,
):
    wm = await WarehouseMapsRepository(session).get_in_warehouse(warehouse_id=warehouse_id, warehouse_map_id=warehouse_map_id)
    if not wm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse map not found")

    user_role = _parse_role(user)
    if role_at_least(user_role, Role.supervisor):
        return wm

    # Object-level access: non-supervisors can only operate on their own maps.
    if wm.created_by_user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    # Read is always ok for the owner; writes are ok for the owner too.
    if write:
        return wm
    return wm


@router.post("/{warehouse_id}/maps", response_model=WarehouseMapOut, status_code=status.HTTP_201_CREATED)
async def create_warehouse_map(
    warehouse_id: uuid.UUID,
    payload: WarehouseMapCreate,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> WarehouseMapOut:
    await _require_warehouse(warehouse_id=warehouse_id, session=session)
    wm = await WarehouseMapsRepository(session).create(
        warehouse_id=warehouse_id,
        created_by_user_id=user.id,
        name=payload.name,
        locations=payload.locations,
    )
    await session.commit()
    return WarehouseMapOut.model_validate(wm)


@router.get("/{warehouse_id}/maps", response_model=list[WarehouseMapOut])
async def list_warehouse_maps(
    warehouse_id: uuid.UUID,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[WarehouseMapOut]:
    await _require_warehouse(warehouse_id=warehouse_id, session=session)
    user_role = _parse_role(user)
    created_by_user_id: uuid.UUID | None = None
    if not role_at_least(user_role, Role.supervisor):
        created_by_user_id = user.id
    maps = await WarehouseMapsRepository(session).list_by_warehouse(
        warehouse_id=warehouse_id, limit=limit, offset=offset, created_by_user_id=created_by_user_id
    )
    return [WarehouseMapOut.model_validate(m) for m in maps]


@router.get("/{warehouse_id}/maps/{warehouse_map_id}", response_model=WarehouseMapOut)
async def get_warehouse_map(
    warehouse_id: uuid.UUID,
    warehouse_map_id: uuid.UUID,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> WarehouseMapOut:
    await _require_warehouse(warehouse_id=warehouse_id, session=session)
    wm = await _require_map_access(
        warehouse_id=warehouse_id, warehouse_map_id=warehouse_map_id, user=user, session=session, write=False
    )
    return WarehouseMapOut.model_validate(wm)


@router.patch("/{warehouse_id}/maps/{warehouse_map_id}", response_model=WarehouseMapOut)
async def update_warehouse_map(
    warehouse_id: uuid.UUID,
    warehouse_map_id: uuid.UUID,
    payload: WarehouseMapUpdate,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> WarehouseMapOut:
    await _require_warehouse(warehouse_id=warehouse_id, session=session)
    wm = await _require_map_access(
        warehouse_id=warehouse_id, warehouse_map_id=warehouse_map_id, user=user, session=session, write=True
    )
    wm = await WarehouseMapsRepository(session).patch(wm, name=payload.name, locations=payload.locations)
    await session.commit()
    return WarehouseMapOut.model_validate(wm)


@router.delete("/{warehouse_id}/maps/{warehouse_map_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_warehouse_map(
    warehouse_id: uuid.UUID,
    warehouse_map_id: uuid.UUID,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> None:
    await _require_warehouse(warehouse_id=warehouse_id, session=session)
    wm = await _require_map_access(
        warehouse_id=warehouse_id, warehouse_map_id=warehouse_map_id, user=user, session=session, write=True
    )
    object_key = (wm.mesh_object_key or "").lstrip("/")
    if object_key:
        try:
            await S3Service().delete_object_async(object_key=object_key)
        except Exception:
            pass
    await WarehouseMapsRepository(session).delete(warehouse_map_id=warehouse_map_id)
    await session.commit()
    return None


@router.post("/{warehouse_id}/maps/{warehouse_map_id}/mesh/presign", response_model=PresignWarehouseMapMeshResponse)
async def presign_warehouse_map_mesh_upload(
    warehouse_id: uuid.UUID,
    warehouse_map_id: uuid.UUID,
    payload: PresignWarehouseMapMeshRequest,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PresignWarehouseMapMeshResponse:
    await _require_warehouse(warehouse_id=warehouse_id, session=session)
    wm = await _require_map_access(
        warehouse_id=warehouse_id, warehouse_map_id=warehouse_map_id, user=user, session=session, write=True
    )

    # Some clients include optional parameters like `; charset=utf-8` which will break
    # presigned URL signatures. Normalize to the media type portion.
    content_type = payload.content_type.split(";", 1)[0].strip().lower()
    if content_type not in ALLOWED_MESH_CONTENT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported content_type")

    existing = wm.mesh_object_key
    if existing:
        object_key = existing.lstrip("/")
    else:
        filename = (payload.filename or "warehouse-map").strip()
        filename = re.sub(r"[^A-Za-z0-9._-]+", "_", filename)[:100].strip("._-") or "warehouse-map"
        filename_lower = filename.lower()
        name_ext = f".{filename_lower.rsplit('.', 1)[-1]}" if "." in filename_lower else ""

        if content_type == "application/octet-stream" and name_ext not in {".ply", ".obj"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="application/octet-stream is only allowed for .ply and .obj meshes",
            )

        ext = ".glb" if content_type == "model/gltf-binary" else ".gltf" if content_type == "model/gltf+json" else ""
        if content_type == "application/octet-stream":
            ext = name_ext

        if ext and filename_lower.endswith(ext):
            filename = filename[: -len(ext)]
            filename = filename.rstrip("._-") or "warehouse-map"

        object_key = f"warehouse-maps/{warehouse_id}/{warehouse_map_id}/{uuid.uuid4().hex}-{filename}{ext}"
        wm.mesh_object_key = object_key
        await session.commit()

    url = S3Service().presign_put_url(object_key=object_key, content_type=content_type)
    return PresignWarehouseMapMeshResponse(
        method="PUT",
        url=url,
        headers={"Content-Type": content_type},
        expires_in_seconds=settings.S3_PRESIGN_EXPIRES_SECONDS,
        object_key=object_key,
    )


@router.post("/{warehouse_id}/maps/{warehouse_map_id}/mesh/confirm", response_model=ConfirmWarehouseMapMeshResponse)
async def confirm_warehouse_map_mesh_upload(
    warehouse_id: uuid.UUID,
    warehouse_map_id: uuid.UUID,
    payload: ConfirmWarehouseMapMeshRequest,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ConfirmWarehouseMapMeshResponse:
    await _require_warehouse(warehouse_id=warehouse_id, session=session)
    wm = await _require_map_access(
        warehouse_id=warehouse_id, warehouse_map_id=warehouse_map_id, user=user, session=session, write=True
    )

    object_key = (wm.mesh_object_key or "").lstrip("/")
    if not object_key:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Warehouse map has no mesh object")

    meta = await S3Service().head_object_async(object_key=object_key)
    if not meta:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Mesh object not found")

    etag: str | None = meta.get("etag") if isinstance(meta, dict) else None
    size: int | None = meta.get("bytes") if isinstance(meta, dict) else None
    stored_content_type: str | None = meta.get("content_type") if isinstance(meta, dict) else None

    if stored_content_type and stored_content_type.lower() not in ALLOWED_MESH_CONTENT_TYPES:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported mesh Content-Type in storage")

    if payload.etag and etag and payload.etag.strip().strip('"') != etag:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ETag mismatch")
    if payload.bytes is not None and size is not None and payload.bytes != size:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Size mismatch")

    wm.mesh_etag = etag or (payload.etag.strip().strip('"') if payload.etag else None)
    wm.mesh_bytes = size or payload.bytes
    # Treat confirm as "this upload is now live". If the object was overwritten, update the timestamp.
    wm.mesh_uploaded_at = datetime.now(timezone.utc)
    await session.commit()

    return ConfirmWarehouseMapMeshResponse(
        warehouse_map_id=wm.id,
        object_key=object_key,
        etag=wm.mesh_etag,
        bytes=wm.mesh_bytes,
        uploaded_at=wm.mesh_uploaded_at,
    )


@router.get("/{warehouse_id}/maps/{warehouse_map_id}/mesh/download", response_model=WarehouseMapMeshDownloadResponse)
async def download_warehouse_map_mesh(
    warehouse_id: uuid.UUID,
    warehouse_map_id: uuid.UUID,
    user=Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> WarehouseMapMeshDownloadResponse:
    await _require_warehouse(warehouse_id=warehouse_id, session=session)
    wm = await _require_map_access(
        warehouse_id=warehouse_id, warehouse_map_id=warehouse_map_id, user=user, session=session, write=False
    )

    object_key = (wm.mesh_object_key or "").lstrip("/")
    if not object_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Warehouse map has no mesh object")

    meta = await S3Service().head_object_async(object_key=object_key)
    if not meta:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Mesh object not found")

    url = S3Service().presign_get_url(object_key=object_key)
    return WarehouseMapMeshDownloadResponse(url=url, expires_in_seconds=settings.S3_PRESIGN_EXPIRES_SECONDS)
