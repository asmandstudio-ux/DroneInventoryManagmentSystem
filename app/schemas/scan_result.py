from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ScanResultCreate(BaseModel):
    mission_id: uuid.UUID
    drone_id: str | None = Field(default=None, max_length=64)
    data: dict[str, Any] = Field(default_factory=dict)


class ScanResultOut(BaseModel):
    id: uuid.UUID
    mission_id: uuid.UUID
    drone_id: str | None
    captured_at: datetime
    data: dict[str, Any]
    evidence_object_key: str | None
    evidence_etag: str | None
    evidence_bytes: int | None
    evidence_uploaded_at: datetime | None

    model_config = {"from_attributes": True}

