import unittest
from typing import Dict, List, Sequence, Tuple

import numpy as np

from app.ai_engine.barcode_pipeline import BarcodePipelineConfig, BarcodePipelineMVP
from app.ai_engine.barcode_types import BBoxXYXY, DecodedBarcode, Detection
from app.ai_engine.dedupe import BurstDedupeConfig, SimpleBurstDedupeTask
from app.ai_engine.preprocess import OpenCVPreprocessTask


class _FakeDetector:
    def __call__(self, frame_bgr: np.ndarray) -> Tuple[List[Detection], Dict[str, float]]:
        h, w = frame_bgr.shape[:2]
        # A deterministic bbox near the center.
        bbox = BBoxXYXY(x1=w // 4, y1=h // 3, x2=(3 * w) // 4, y2=(2 * h) // 3)
        return [Detection(bbox=bbox, confidence=0.9, class_id=0, class_name="barcode")], {"inference_ms": 1.0}


class _FakeDecoder:
    def __init__(self, payloads_per_frame: Sequence[Sequence[str]]):
        self._payloads = payloads_per_frame

    def __call__(
        self,
        frame_bgr: np.ndarray,
        preprocessed_gray: np.ndarray,
        detections: Sequence[Detection],
    ) -> Tuple[List[DecodedBarcode], Dict[str, float]]:
        # Use the first detection as the bbox reference.
        bbox = detections[0].bbox if detections else None
        # Encode frame index in a pixel for test determinism:
        # (not used, but ensures we can "vary" output based on call order)
        frame_index = int(frame_bgr[0, 0, 0])
        payloads = self._payloads[frame_index]
        out = [DecodedBarcode(data=p, symbology="QRCODE", bbox=bbox, confidence=0.8) for p in payloads]
        return out, {"decode_ms": 0.5}


class TestOpenCVPreprocessTask(unittest.TestCase):
    def test_preprocess_outputs_grayscale_same_size(self) -> None:
        img = np.zeros((240, 320, 3), dtype=np.uint8)
        img[:, :] = (10, 20, 30)
        task = OpenCVPreprocessTask()
        out, metrics = task(img)
        self.assertEqual(out.shape, (240, 320))
        self.assertEqual(out.dtype, np.uint8)
        self.assertIn("blur_var", metrics)
        self.assertIn("mean_intensity", metrics)

    def test_preprocess_rejects_invalid_shape(self) -> None:
        task = OpenCVPreprocessTask()
        with self.assertRaises(ValueError):
            task(np.zeros((10, 10), dtype=np.uint8))  # type: ignore[arg-type]


class TestSimpleBurstDedupe(unittest.TestCase):
    def test_dedupe_requires_confirmations(self) -> None:
        deduper = SimpleBurstDedupeTask(BurstDedupeConfig(min_confirmations=2))

        f0 = [DecodedBarcode(data="A", symbology="QRCODE"), DecodedBarcode(data="B", symbology="QRCODE")]
        f1 = [DecodedBarcode(data="A", symbology="QRCODE")]
        frames = [
            _frame_result(0, f0),
            _frame_result(1, f1),
        ]

        unique, metrics = deduper(frames)
        self.assertEqual([u.data for u in unique], ["A"])
        self.assertEqual(int(metrics["unique_confirmed"]), 1)


class TestBarcodePipelineMVP(unittest.TestCase):
    def test_pipeline_dedupes_across_burst(self) -> None:
        frames = _make_burst(3)
        # Frame 0 -> A, Frame 1 -> A, Frame 2 -> C
        decoder = _FakeDecoder(payloads_per_frame=[["A"], ["A"], ["C"]])
        pipe = BarcodePipelineMVP(
            detector=_FakeDetector(),
            decoder=decoder,
            preprocess=OpenCVPreprocessTask(),
            config=BarcodePipelineConfig(min_confirmations=2),
        )

        res = pipe.process_burst(frames)
        self.assertEqual([b.data for b in res.unique], ["A"])
        self.assertEqual(len(res.frames), 3)
        # Ensure metrics are present.
        self.assertIn("dedupe_unique_confirmed", res.meta)


def _frame_result(idx: int, decoded: List[DecodedBarcode]):
    from app.ai_engine.barcode_types import FrameScanResult

    return FrameScanResult(frame_index=idx, detections=[], decoded=decoded, meta={})


def _make_burst(n: int) -> List[np.ndarray]:
    frames: List[np.ndarray] = []
    for i in range(n):
        img = np.zeros((120, 160, 3), dtype=np.uint8)
        img[0, 0, 0] = i  # encode index for _FakeDecoder
        frames.append(img)
    return frames


if __name__ == "__main__":
    unittest.main()

