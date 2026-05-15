from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Optional, Protocol, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


class PreprocessTask(Protocol):
    """Preprocesses a BGR frame into an image more suitable for barcode decoding."""

    def __call__(self, frame_bgr: np.ndarray) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Args:
            frame_bgr: HxWx3 BGR uint8 frame.

        Returns:
            preprocessed: HxW uint8 image (typically grayscale).
            metrics: dictionary of lightweight metrics (blur score, brightness, etc.).
        """


@dataclass(frozen=True)
class OpenCVPreprocessConfig:
    clahe_clip_limit: float = 2.0
    clahe_grid_size: Tuple[int, int] = (8, 8)
    blur_var_threshold: float = 60.0  # below => likely motion blur / out-of-focus
    unsharp_strength: float = 1.2
    unsharp_strength_blurry: float = 2.0
    gamma_min: float = 0.6
    gamma_max: float = 1.6


def _laplacian_variance(gray: np.ndarray) -> float:
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def _mean_intensity(gray: np.ndarray) -> float:
    return float(np.mean(gray))


def _gamma_correct(gray: np.ndarray, gamma: float) -> np.ndarray:
    inv_gamma = 1.0 / max(1e-6, gamma)
    table = (np.arange(256) / 255.0) ** inv_gamma
    table = np.clip(table * 255.0, 0, 255).astype(np.uint8)
    return cv2.LUT(gray, table)


@dataclass
class OpenCVPreprocessTask:
    """
    Warehouse/drone-friendly preprocessing:
    - Convert to grayscale
    - Adaptive gamma correction based on brightness
    - CLAHE for local contrast
    - Unsharp mask, stronger when blur is detected
    """

    cfg: OpenCVPreprocessConfig = OpenCVPreprocessConfig()

    def __call__(self, frame_bgr: np.ndarray) -> Tuple[np.ndarray, Dict[str, float]]:
        if frame_bgr is None or frame_bgr.size == 0:
            raise ValueError("frame_bgr is empty")

        if frame_bgr.ndim != 3 or frame_bgr.shape[2] != 3:
            raise ValueError(f"Expected BGR image HxWx3, got shape={frame_bgr.shape}")

        gray = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2GRAY)

        blur_var = _laplacian_variance(gray)
        mean_int = _mean_intensity(gray)

        # Gamma heuristic: brighten dark frames, darken overexposed frames.
        # mean_int ~ [0..255]; map to gamma in [gamma_min, gamma_max].
        # Dark => gamma > 1, Bright => gamma < 1.
        t = np.clip(mean_int / 255.0, 0.0, 1.0)
        gamma = float(self.cfg.gamma_max - t * (self.cfg.gamma_max - self.cfg.gamma_min))
        gray = _gamma_correct(gray, gamma=gamma)

        clahe = cv2.createCLAHE(
            clipLimit=float(self.cfg.clahe_clip_limit),
            tileGridSize=tuple(self.cfg.clahe_grid_size),
        )
        gray = clahe.apply(gray)

        # Unsharp mask (sharpening), stronger when blur is suspected.
        strength = (
            self.cfg.unsharp_strength_blurry
            if blur_var < self.cfg.blur_var_threshold
            else self.cfg.unsharp_strength
        )
        blurred = cv2.GaussianBlur(gray, (0, 0), sigmaX=1.0)
        sharp = cv2.addWeighted(gray, 1.0 + strength, blurred, -strength, 0)

        # Optional light denoise to reduce speckle; keep it cheap.
        sharp = cv2.fastNlMeansDenoising(sharp, None, h=7, templateWindowSize=7, searchWindowSize=21)

        metrics = {
            "blur_var": float(blur_var),
            "mean_intensity": float(mean_int),
            "gamma": float(gamma),
            "unsharp_strength": float(strength),
        }
        return sharp, metrics

