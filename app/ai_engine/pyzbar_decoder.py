from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol, Sequence, Tuple

import cv2
import numpy as np

from .barcode_types import BBoxXYXY, DecodedBarcode, Detection, crop_bbox

logger = logging.getLogger(__name__)


class DecodeTask(Protocol):
    """Decodes barcodes from detected regions."""

    def __call__(
        self,
        frame_bgr: np.ndarray,
        preprocessed_gray: np.ndarray,
        detections: Sequence[Detection],
    ) -> Tuple[List[DecodedBarcode], Dict[str, float]]:
        """Return decoded barcodes for a single frame."""


@dataclass(frozen=True)
class PyzbarDecodeConfig:
    pad: int = 8
    min_crop_size: int = 24
    try_binarize: bool = True
    try_rotations: Tuple[int, ...] = (0, 90, 180, 270)
    max_regions: int = 25


class PyzbarDecodeTask:
    def __init__(self, cfg: PyzbarDecodeConfig = PyzbarDecodeConfig()):
        self.cfg = cfg
        try:
            from pyzbar.pyzbar import decode as zbar_decode  # type: ignore
        except Exception as e:  # pragma: no cover
            raise ImportError(
                "pyzbar is required for PyzbarDecodeTask. "
                "Install with: pip install pyzbar (and ensure zbar is installed)."
            ) from e

        self._zbar_decode = zbar_decode

    def __call__(
        self,
        frame_bgr: np.ndarray,
        preprocessed_gray: np.ndarray,
        detections: Sequence[Detection],
    ) -> Tuple[List[DecodedBarcode], Dict[str, float]]:
        import time

        t0 = time.perf_counter()

        if preprocessed_gray.ndim != 2:
            raise ValueError("preprocessed_gray must be grayscale HxW")

        # Prioritize high confidence and limit work.
        dets = sorted(detections, key=lambda d: d.confidence, reverse=True)[: self.cfg.max_regions]

        decoded: List[DecodedBarcode] = []

        for det in dets:
            bbox = det.bbox
            # Crop from preprocessed grayscale for decoding stability.
            crop = crop_bbox(preprocessed_gray, bbox, pad=self.cfg.pad)
            if crop.size == 0:
                continue
            if min(crop.shape[:2]) < self.cfg.min_crop_size:
                continue

            decoded.extend(self._decode_crop(crop=crop, det=det))

        metrics = {"decode_ms": (time.perf_counter() - t0) * 1000.0}
        return decoded, metrics

    def _decode_crop(self, crop: np.ndarray, det: Detection) -> List[DecodedBarcode]:
        out: List[DecodedBarcode] = []

        # Build a small set of candidate images to try.
        candidates: List[Tuple[str, np.ndarray]] = [("gray", crop)]

        if self.cfg.try_binarize:
            # Otsu threshold is cheap and frequently helps in warehouses (specular highlights / low contrast).
            _, thr = cv2.threshold(crop, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            candidates.append(("otsu", thr))

        for rotation in self.cfg.try_rotations:
            for tag, img in candidates:
                img2 = img if rotation == 0 else self._rotate_90(img, rotation)
                try:
                    symbols = self._zbar_decode(img2)
                except Exception:
                    # Guard against occasional zbar errors on bad crops.
                    logger.exception("pyzbar decode failed")
                    continue

                for sym in symbols:
                    try:
                        payload = sym.data.decode("utf-8", errors="replace")
                    except Exception:
                        payload = str(sym.data)
                    symbology = str(getattr(sym, "type", "UNKNOWN"))
                    out.append(
                        DecodedBarcode(
                            data=payload,
                            symbology=symbology,
                            bbox=det.bbox,
                            confidence=det.confidence,
                            meta={"variant": tag, "rotation": rotation},
                        )
                    )

            # Early exit if something decoded at this rotation.
            if out:
                break

        return out

    @staticmethod
    def _rotate_90(img: np.ndarray, degrees: int) -> np.ndarray:
        deg = degrees % 360
        if deg == 0:
            return img
        if deg == 90:
            return cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
        if deg == 180:
            return cv2.rotate(img, cv2.ROTATE_180)
        if deg == 270:
            return cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
        # Fallback for non-right angles (shouldn't happen with our default config).
        h, w = img.shape[:2]
        m = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), degrees, 1.0)
        return cv2.warpAffine(img, m, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

