from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class WarehouseMapBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    locations: dict = Field(default_factory=dict)


class WarehouseMapCreate(WarehouseMapBase):
    pass


class WarehouseMapUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    locations: dict | None = None


class WarehouseMapOut(WarehouseMapBase):
    id: uuid.UUID
    warehouse_id: uuid.UUID
    created_by_user_id: uuid.UUID

    mesh_object_key: str | None = None
    mesh_etag: str | None = None
    mesh_bytes: int | None = None
    mesh_uploaded_at: datetime | None = None

    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PresignWarehouseMapMeshRequest(BaseModel):
    content_type: str = Field(min_length=3, max_length=255)
    filename: str | None = Field(default=None, max_length=255)


class PresignWarehouseMapMeshResponse(BaseModel):
    method: str = "PUT"
    url: str
    headers: dict[str, str] = Field(default_factory=dict)
    expires_in_seconds: int
    object_key: str


class ConfirmWarehouseMapMeshRequest(BaseModel):
    etag: str | None = Field(default=None, max_length=128)
    bytes: int | None = Field(default=None, ge=0)


class ConfirmWarehouseMapMeshResponse(BaseModel):
    warehouse_map_id: uuid.UUID
    object_key: str
    etag: str | None = None
    bytes: int | None = None
    uploaded_at: datetime


class WarehouseMapMeshDownloadResponse(BaseModel):
    url: str
    expires_in_seconds: int
