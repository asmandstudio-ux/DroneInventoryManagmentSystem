from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class PresignUploadRequest(BaseModel):
    scan_result_id: uuid.UUID
    content_type: str = Field(min_length=3, max_length=255)
    filename: str | None = Field(default=None, max_length=255)


class PresignUploadResponse(BaseModel):
    method: str = "PUT"
    url: str
    headers: dict[str, str] = Field(default_factory=dict)
    expires_in_seconds: int
    object_key: str


class ConfirmUploadRequest(BaseModel):
    scan_result_id: uuid.UUID
    etag: str | None = Field(default=None, max_length=128)
    bytes: int | None = Field(default=None, ge=0)


class ConfirmUploadResponse(BaseModel):
    scan_result_id: uuid.UUID
    object_key: str
    etag: str | None = None
    bytes: int | None = None
    uploaded_at: datetime
    scan_job_id: uuid.UUID | None = None

