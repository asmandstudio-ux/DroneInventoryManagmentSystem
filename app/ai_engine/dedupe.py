from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Iterable, List, Protocol, Sequence, Tuple

from .barcode_types import DecodedBarcode, FrameScanResult

logger = logging.getLogger(__name__)


class BurstDedupeTask(Protocol):
    """Deduplicates decoded barcodes across a burst of frames."""

    def __call__(self, frame_results: Sequence[FrameScanResult]) -> Tuple[List[DecodedBarcode], Dict[str, float]]:
        """
        Returns:
            unique: unique barcodes in the burst.
            metrics: lightweight metrics (counts, etc.).
        """


@dataclass(frozen=True)
class BurstDedupeConfig:
    # Require multiple frame confirmations to reduce false positives from blur / partial occlusion.
    min_confirmations: int = 2
    # If true, treat (symbology, data) as unique key. Otherwise dedupe by data only.
    key_include_symbology: bool = False
    # Cap how many unique codes we return to protect downstream systems.
    max_unique: int = 200


class SimpleBurstDedupeTask:
    """
    Simple burst dedupe:
    - Aggregates by barcode payload (optionally includes symbology)
    - Keeps the "best" representative instance (highest confidence) per key
    - Filters keys not seen at least `min_confirmations` times across frames
    """

    def __init__(self, cfg: BurstDedupeConfig = BurstDedupeConfig()):
        self.cfg = cfg

    def __call__(self, frame_results: Sequence[FrameScanResult]) -> Tuple[List[DecodedBarcode], Dict[str, float]]:
        counts: Dict[str, int] = {}
        best: Dict[str, DecodedBarcode] = {}

        total_decoded = 0
        for fr in frame_results:
            # Avoid double-counting within a single frame by unique keys.
            seen_keys_in_frame = set()
            for b in fr.decoded:
                total_decoded += 1
                key = self._key(b)
                if key in seen_keys_in_frame:
                    continue
                seen_keys_in_frame.add(key)
                counts[key] = counts.get(key, 0) + 1

                # Keep best confidence (or first if None).
                prev = best.get(key)
                if prev is None:
                    best[key] = b
                else:
                    prev_conf = prev.confidence if prev.confidence is not None else -1.0
                    b_conf = b.confidence if b.confidence is not None else -1.0
                    if b_conf > prev_conf:
                        best[key] = b

        confirmed = [
            best[k]
            for k, c in counts.items()
            if c >= int(self.cfg.min_confirmations) and k in best
        ]

        # Sort stable: highest confidence first, then lexicographically.
        confirmed.sort(
            key=lambda b: (
                -(b.confidence if b.confidence is not None else 0.0),
                b.symbology,
                b.data,
            )
        )

        if len(confirmed) > self.cfg.max_unique:
            confirmed = confirmed[: self.cfg.max_unique]

        metrics = {
            "frames": float(len(frame_results)),
            "total_decoded": float(total_decoded),
            "unique_candidates": float(len(best)),
            "unique_confirmed": float(len(confirmed)),
        }
        return confirmed, metrics

    def _key(self, b: DecodedBarcode) -> str:
        if self.cfg.key_include_symbology:
            return f"{b.symbology}::{b.data}"
        return b.data

