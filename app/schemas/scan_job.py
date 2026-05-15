from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ScanJobOut(BaseModel):
    id: uuid.UUID
    scan_result_id: uuid.UUID
    status: str
    result: dict
    error_message: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ScanJobCreate(BaseModel):
    scan_result_id: uuid.UUID
