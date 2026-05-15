from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.mission import MissionStatus


class MissionCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str | None = None
    priority: int = Field(default=100, ge=1, le=1000)
    drone_id: str | None = Field(default=None, max_length=64)
    waypoints: dict[str, Any] = Field(default_factory=dict)


class MissionUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = None
    priority: int | None = Field(default=None, ge=1, le=1000)
    drone_id: str | None = Field(default=None, max_length=64)
    waypoints: dict[str, Any] | None = None


class MissionStatusUpdate(BaseModel):
    status: MissionStatus


class MissionOut(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    status: MissionStatus
    priority: int
    drone_id: str | None
    waypoints: dict[str, Any]
    created_by_user_id: uuid.UUID
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

