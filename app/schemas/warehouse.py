from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import AliasChoices, BaseModel, Field


class WarehouseBase(BaseModel):
    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=200)
    address: str | None = None
    metadata: dict = Field(
        default_factory=dict,
        validation_alias=AliasChoices("metadata", "meta"),
        serialization_alias="metadata",
    )


class WarehouseCreate(WarehouseBase):
    pass


class WarehouseUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=32)
    name: str | None = Field(default=None, min_length=1, max_length=200)
    address: str | None = None
    metadata: dict | None = Field(
        default=None,
        validation_alias=AliasChoices("metadata", "meta"),
        serialization_alias="metadata",
    )


class WarehouseOut(WarehouseBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
