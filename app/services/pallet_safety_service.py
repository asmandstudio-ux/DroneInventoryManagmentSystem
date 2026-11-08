from __future__ import annotations

import logging
import os
from typing import Any, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class PalletModelUnavailable(RuntimeError):
    """Raised when a pallet check needs the ONNX model but it (or onnxruntime) is missing."""


class PalletSafetyService:
    """
    Server-side pallet lean / stack safety check.

    Wraps the self-contained ``pallet_safety`` library (Hover Logix YOLO26n ONNX detector +
    straight-box lean measurement). The model file and ``onnxruntime`` are OPTIONAL: when either
    is absent the service reports ``available = False`` and model-based checks raise
    :class:`PalletModelUnavailable`, so importing this module never pulls heavy deps and the API
    stays up. The ONNX session is built lazily on first use and then reused.

    Reviewer-drawn boxes (:meth:`analyse_boxes`) are measured WITHOUT the model, so that path
    works even where onnxruntime is not installed (``pallet_safety`` only imports onnxruntime
    inside ``Detector.__init__``).
    """

    def __init__(self, model_path: Optional[str] = None) -> None:
        self._model_path = model_path or settings.PALLET_MODEL_PATH
        self._detector: Any = None
        self._load_error: Optional[str] = None

    @property
    def model_path(self) -> str:
        return self._model_path

    @property
    def model_version(self) -> str:
        """Short tag for the detector that produced a result (the model file stem)."""
        return os.path.splitext(os.path.basename(self._model_path))[0]

    def _ensure_detector(self) -> Any:
        if self._detector is not None:
            return self._detector
        if not os.path.exists(self._model_path):
            self._load_error = f"model file not found: {self._model_path}"
            return None
        try:
            from pallet_safety import Detector

            self._detector = Detector(self._model_path)
            self._load_error = None
            logger.info("Pallet-safety ONNX model loaded from %s", self._model_path)
        except Exception as exc:  # onnxruntime missing / unreadable model
            self._load_error = f"{type(exc).__name__}: {exc}"
            self._detector = None
            logger.warning("Pallet-safety model unavailable: %s", self._load_error)
        return self._detector

    def status(self) -> dict[str, Any]:
        detector = self._ensure_detector()
        return {
            "available": detector is not None,
            "model_path": self._model_path,
            "model_present": os.path.exists(self._model_path),
            "error": self._load_error,
        }

    @staticmethod
    def _decode(image_bytes: bytes):
        import cv2
        import numpy as np

        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("could not decode image (unsupported or corrupt file)")
        return img

    @staticmethod
    def _limits(overrides: Optional[dict]):
        from pallet_safety import Limits

        clean = {k: v for k, v in (overrides or {}).items() if v is not None}
        return Limits(**clean) if clean else None

    def analyse(
        self,
        image_bytes: bytes,
        *,
        limits: Optional[dict] = None,
        reference: Any = "auto",
    ) -> dict[str, Any]:
        """Run the model and measure every pallet/stack. Raises PalletModelUnavailable if no model."""
        from pallet_safety import analyse_image

        detector = self._ensure_detector()
        if detector is None:
            raise PalletModelUnavailable(self._load_error or "pallet model unavailable")
        img = self._decode(image_bytes)
        return analyse_image(img, detector, self._limits(limits), reference=reference)

    def analyse_boxes(
        self,
        image_bytes: bytes,
        boxes: list[list[float]],
        *,
        limits: Optional[dict] = None,
    ) -> dict[str, Any]:
        """Measure reviewer-drawn pallet boxes without running the model (no onnxruntime needed)."""
        from pallet_safety import analyse_image

        img = self._decode(image_bytes)
        return analyse_image(img, limits=self._limits(limits), pallet_boxes=boxes)


# Singleton — construction is cheap (no heavy imports, no model load until first use).
pallet_safety_service = PalletSafetyService()
