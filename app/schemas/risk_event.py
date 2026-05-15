from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.risk_event import RiskSeverity


class RiskEventCreate(BaseModel):
    mission_id: uuid.UUID | None = None
    scan_result_id: uuid.UUID | None = None
    drone_id: str | None = Field(default=None, max_length=64)

    severity: RiskSeverity = RiskSeverity.medium
    category: str = Field(min_length=1, max_length=64)
    message: str = Field(min_length=1, max_length=10_000)
    details: dict = Field(default_factory=dict)


class RiskEventOut(BaseModel):
    id: uuid.UUID
    mission_id: uuid.UUID | None
    scan_result_id: uuid.UUID | None
    drone_id: str | None
    severity: str
    category: str
    message: str
    details: dict
    created_at: datetime

    model_config = {"from_attributes": True}

