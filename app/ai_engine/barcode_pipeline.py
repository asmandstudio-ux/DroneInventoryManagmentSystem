from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import numpy as np

from .barcode_types import BurstScanResult, FrameScanResult
from .dedupe import BurstDedupeConfig, SimpleBurstDedupeTask
from .preprocess import OpenCVPreprocessConfig, OpenCVPreprocessTask, PreprocessTask
from .pyzbar_decoder import DecodeTask
from .yolo_detector import RegionDetectTask

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BarcodePipelineConfig:
    """
    MVP barcode pipeline config (warehouse drone).

    Notes:
    - YOLO detector and decoder are injected, so the pipeline is testable without
      ultralytics/pyzbar installed.
    """

    # Minimum decoded confirmations across burst frames to accept a barcode.
    min_confirmations: int = 2
    # If True, include symbology in dedupe key.
    key_include_symbology: bool = False


class BarcodePipelineMVP:
    """
    Pipeline: capture -> OpenCV preprocess -> YOLOv8 region detect -> pyzbar decode -> burst dedupe.
    """

    def __init__(
        self,
        detector: RegionDetectTask,
        decoder: DecodeTask,
        preprocess: Optional[PreprocessTask] = None,
        config: BarcodePipelineConfig = BarcodePipelineConfig(),
    ):
        self.detector = detector
        self.decoder = decoder
        self.preprocess = preprocess or OpenCVPreprocessTask(OpenCVPreprocessConfig())
        self.config = config
        self._deduper = SimpleBurstDedupeTask(
            BurstDedupeConfig(
                min_confirmations=int(config.min_confirmations),
                key_include_symbology=bool(config.key_include_symbology),
            )
        )

    def process_frame(self, frame_bgr: np.ndarray, frame_index: int) -> FrameScanResult:
        """
        Args:
            frame_bgr: HxWx3 uint8 BGR
            frame_index: index within burst
        """
        pre, pre_metrics = self.preprocess(frame_bgr)
        dets, det_metrics = self.detector(frame_bgr)
        decoded, dec_metrics = self.decoder(frame_bgr, pre, dets)

        meta: Dict[str, float] = {}
        meta.update({f"pre_{k}": float(v) for k, v in pre_metrics.items()})
        meta.update({f"det_{k}": float(v) for k, v in det_metrics.items()})
        meta.update({f"dec_{k}": float(v) for k, v in dec_metrics.items()})

        return FrameScanResult(frame_index=frame_index, detections=dets, decoded=decoded, meta=meta)

    def process_burst(self, frames_bgr: Sequence[np.ndarray]) -> BurstScanResult:
        """
        Process a short burst (N frames) from the drone camera and return deduped codes.
        """
        frame_results: List[FrameScanResult] = []
        for idx, frame in enumerate(frames_bgr):
            frame_results.append(self.process_frame(frame, frame_index=idx))

        unique, dedupe_metrics = self._deduper(frame_results)
        meta: Dict[str, float] = {f"dedupe_{k}": float(v) for k, v in dedupe_metrics.items()}

        return BurstScanResult(frames=frame_results, unique=unique, meta=meta)

