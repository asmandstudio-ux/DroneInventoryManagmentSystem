from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.report_job import ReportJobStatus


class ReportJobCreate(BaseModel):
    report_type: str = Field(min_length=2, max_length=64)
    params: dict[str, Any] = Field(default_factory=dict)


class ReportJobOut(BaseModel):
    id: uuid.UUID
    report_type: str
    params: dict[str, Any]
    status: ReportJobStatus
    created_by_user_id: uuid.UUID
    result_object_key: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PresignDownloadResponse(BaseModel):
    url: str
    expires_in_seconds: int

