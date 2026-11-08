from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class PalletReviewCreate(BaseModel):
    pallet_id: str | None = Field(default=None, max_length=16)
    call: str | None = Field(default=None, max_length=32)
    lines: dict[str, Any] | None = None


class PalletReviewOut(BaseModel):
    id: uuid.UUID
    check_id: uuid.UUID
    reviewer_user_id: uuid.UUID
    pallet_id: str | None
    call: str | None
    lines: dict[str, Any] | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PalletCheckOut(BaseModel):
    id: uuid.UUID
    created_by_user_id: uuid.UUID
    warehouse_id: uuid.UUID | None
    location_code: str | None
    overall: str | None
    model_version: str | None
    result: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class PalletCheckSummary(BaseModel):
    """List view — omits the large ``result`` blob."""

    id: uuid.UUID
    warehouse_id: uuid.UUID | None
    location_code: str | None
    overall: str | None
    model_version: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
