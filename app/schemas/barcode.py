from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class BarcodeReadOut(BaseModel):
    id: uuid.UUID
    scan_result_id: uuid.UUID
    symbology: str
    value: str
    confidence: float
    meta: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class BarcodeDecodeRequest(BaseModel):
    pass
