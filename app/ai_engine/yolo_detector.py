from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol, Tuple

import numpy as np

from .barcode_types import BBoxXYXY, Detection

logger = logging.getLogger(__name__)


class RegionDetectTask(Protocol):
    """Detects candidate barcode regions in an image."""

    def __call__(self, frame_bgr: np.ndarray) -> Tuple[List[Detection], Dict[str, float]]:
        """
        Args:
            frame_bgr: HxWx3 uint8 BGR frame.

        Returns:
            detections: candidate barcode regions (xyxy).
            metrics: lightweight metrics (e.g. inference_ms).
        """


@dataclass(frozen=True)
class YoloV8DetectorConfig:
    weights_path: str
    imgsz: int = 640
    conf: float = 0.25
    iou: float = 0.4
    device: Optional[str] = None  # e.g. "cpu", "0" for GPU id
    max_det: int = 50
    barcode_class_names: Tuple[str, ...] = ("barcode", "qr", "datamatrix")


class YoloV8RegionDetector:
    """
    YOLOv8 region detector wrapper.

    Notes:
    - Uses ultralytics.YOLO under the hood.
    - Expects a weights file trained with barcode-related classes.
    """

    def __init__(self, cfg: YoloV8DetectorConfig):
        self.cfg = cfg
        try:
            from ultralytics import YOLO  # type: ignore
        except Exception as e:  # pragma: no cover
            raise ImportError(
                "ultralytics is required for YoloV8RegionDetector. "
                "Install with: pip install ultralytics"
            ) from e

        self._YOLO = YOLO
        self._model = self._YOLO(cfg.weights_path)
        self._names = getattr(self._model, "names", {}) or {}

    def __call__(self, frame_bgr: np.ndarray) -> Tuple[List[Detection], Dict[str, float]]:
        import time

        if frame_bgr is None or frame_bgr.size == 0:
            raise ValueError("frame_bgr is empty")

        t0 = time.perf_counter()

        # ultralytics accepts numpy arrays directly.
        results = self._model.predict(
            source=frame_bgr,
            imgsz=int(self.cfg.imgsz),
            conf=float(self.cfg.conf),
            iou=float(self.cfg.iou),
            device=self.cfg.device,
            max_det=int(self.cfg.max_det),
            verbose=False,
        )

        detections: List[Detection] = []
        h, w = frame_bgr.shape[:2]

        # results is a list with one element for our single image.
        if not results:
            return [], {"inference_ms": (time.perf_counter() - t0) * 1000.0}

        r0 = results[0]
        boxes = getattr(r0, "boxes", None)
        if boxes is None:
            return [], {"inference_ms": (time.perf_counter() - t0) * 1000.0}

        # boxes.xyxy is Nx4 float tensor, boxes.conf and boxes.cls exist.
        xyxy = boxes.xyxy
        confs = boxes.conf
        clss = boxes.cls

        # Convert tensors to numpy without importing torch explicitly.
        xyxy_np = np.asarray(xyxy.cpu() if hasattr(xyxy, "cpu") else xyxy)
        conf_np = np.asarray(confs.cpu() if hasattr(confs, "cpu") else confs)
        cls_np = np.asarray(clss.cpu() if hasattr(clss, "cpu") else clss).astype(int)

        for (x1, y1, x2, y2), conf, cid in zip(xyxy_np, conf_np, cls_np):
            name = str(self._names.get(int(cid), "barcode"))
            # If model has many classes, allow filtering by configured names.
            if self.cfg.barcode_class_names and name not in self.cfg.barcode_class_names:
                continue

            bbox = BBoxXYXY(
                x1=int(round(float(x1))),
                y1=int(round(float(y1))),
                x2=int(round(float(x2))),
                y2=int(round(float(y2))),
            ).clamp(width=w, height=h)
            detections.append(
                Detection(
                    bbox=bbox,
                    confidence=float(conf),
                    class_id=int(cid),
                    class_name=name,
                )
            )

        metrics = {"inference_ms": (time.perf_counter() - t0) * 1000.0}
        return detections, metrics

