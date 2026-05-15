from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np


@dataclass(frozen=True)
class BBoxXYXY:
    """Bounding box in absolute pixel coordinates (x1, y1, x2, y2)."""

    x1: int
    y1: int
    x2: int
    y2: int

    def clamp(self, width: int, height: int) -> "BBoxXYXY":
        x1 = max(0, min(self.x1, width - 1))
        y1 = max(0, min(self.y1, height - 1))
        x2 = max(0, min(self.x2, width - 1))
        y2 = max(0, min(self.y2, height - 1))
        # Ensure correct ordering after clamp.
        if x2 < x1:
            x1, x2 = x2, x1
        if y2 < y1:
            y1, y2 = y2, y1
        return BBoxXYXY(x1=x1, y1=y1, x2=x2, y2=y2)

    def as_tuple(self) -> Tuple[int, int, int, int]:
        return self.x1, self.y1, self.x2, self.y2

    def area(self) -> int:
        return max(0, self.x2 - self.x1) * max(0, self.y2 - self.y1)


@dataclass(frozen=True)
class Detection:
    bbox: BBoxXYXY
    confidence: float
    class_id: int = 0
    class_name: str = "barcode"


@dataclass(frozen=True)
class DecodedBarcode:
    """A decoded barcode payload with provenance."""

    data: str
    symbology: str
    bbox: Optional[BBoxXYXY] = None
    confidence: Optional[float] = None
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FrameScanResult:
    frame_index: int
    detections: List[Detection]
    decoded: List[DecodedBarcode]
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BurstScanResult:
    """Aggregated results across a burst of frames."""

    frames: List[FrameScanResult]
    unique: List[DecodedBarcode]
    meta: Dict[str, Any] = field(default_factory=dict)


def crop_bbox(image: np.ndarray, bbox: BBoxXYXY, pad: int = 0) -> np.ndarray:
    """Crop a bbox region (with optional padding). Returns a view/copy slice."""
    h, w = image.shape[:2]
    b = BBoxXYXY(
        x1=bbox.x1 - pad,
        y1=bbox.y1 - pad,
        x2=bbox.x2 + pad,
        y2=bbox.y2 + pad,
    ).clamp(width=w, height=h)
    # Use +1 indexing safety is not needed; bbox is treated as half-open.
    return image[b.y1 : b.y2, b.x1 : b.x2]

