from __future__ import annotations

import hashlib
from typing import Any

import anyio
import cv2
import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.risk_event import RiskSeverity
from app.repositories.barcode_reads import BarcodeReadsRepository
from app.repositories.risk_events import RiskEventsRepository
from app.repositories.scan_results import ScanResultsRepository
from app.services.s3_service import _client


class BarcodeService:
    """
    Minimal barcode decode service for evidence images stored in S3/MinIO.

    - Keeps decode as a separate service so it can be used by an API endpoint
      or a background worker.
    - Uses a "full-frame" detection (no YOLO dependency) and relies on pyzbar
      for actual decoding.
    """

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.scans = ScanResultsRepository(session)
        self.barcodes = BarcodeReadsRepository(session)
        self.risks = RiskEventsRepository(session)

    async def process_scan_result(self, scan_result_id: Any) -> dict:
        scan = await self.scans.get(scan_result_id)
        if not scan:
            return {"ok": False, "error": "scan_result_not_found"}

        object_key = scan.evidence_object_key
        if not object_key:
            return {"ok": False, "error": "missing_evidence_object_key"}

        try:
            img_bytes = await self._download_object(object_key)
            frame_bgr = self._decode_image_bytes(img_bytes)
            decoded = self._decode_barcodes_full_frame(frame_bgr)
        except Exception as exc:  # noqa: BLE001
            await self.risks.create(
                mission_id=scan.mission_id,
                scan_result_id=scan.id,
                drone_id=scan.drone_id,
                severity=RiskSeverity.high.value,
                category="barcode_decode_error",
                message="Barcode decode failed",
                details={"error": str(exc)[:1024], "object_key": object_key},
            )
            await self.session.flush()
            return {"ok": False, "error": "barcode_decode_failed", "detail": str(exc)}

        # Persist into normalized table + keep a copy in scan_result.data for convenience.
        await self.barcodes.upsert_many(scan_result_id=scan.id, barcodes=decoded)
        scan.data = {**(scan.data or {}), "barcodes": decoded}

        if not decoded:
            await self.risks.create(
                mission_id=scan.mission_id,
                scan_result_id=scan.id,
                drone_id=scan.drone_id,
                severity=RiskSeverity.medium.value,
                category="barcode_not_found",
                message="No barcodes decoded from evidence",
                details={"object_key": object_key},
            )

        await self.session.flush()
        return {"ok": True, "decoded_count": len(decoded), "object_key": object_key}

    async def _download_object(self, object_key: str) -> bytes:
        """
        Download from S3 in a thread to avoid blocking the event loop (boto3 is sync).
        """

        def _get_bytes() -> bytes:
            resp = _client().get_object(Bucket=settings.S3_BUCKET, Key=object_key)
            body = resp["Body"].read()
            # Defensive: allow downstream to dedupe/cache if needed.
            _ = hashlib.sha256(body).hexdigest()
            return body

        return await anyio.to_thread.run_sync(_get_bytes)

    @staticmethod
    def _decode_image_bytes(img_bytes: bytes) -> np.ndarray:
        arr = np.frombuffer(img_bytes, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("Unable to decode image bytes via OpenCV")
        return frame

    @staticmethod
    def _decode_barcodes_full_frame(frame_bgr: np.ndarray) -> list[dict]:
        """
        Decode barcodes without a region detector (full-frame), using pyzbar.
        """

        # Lazy import: allows running API even if pyzbar isn't installed, but will
        # raise a clear error when barcode processing is invoked.
        try:
            from app.ai_engine.barcode_types import BBoxXYXY, Detection
            from app.ai_engine.preprocess import OpenCVPreprocessConfig, OpenCVPreprocessTask
            from app.ai_engine.pyzbar_decoder import PyzbarDecodeConfig, PyzbarDecodeTask
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "Barcode decoding dependencies are missing. Install `pyzbar` and OS zbar libs."
            ) from e

        h, w = frame_bgr.shape[:2]
        preprocess = OpenCVPreprocessTask(OpenCVPreprocessConfig())
        decoder = PyzbarDecodeTask(PyzbarDecodeConfig())

        pre_gray, _metrics = preprocess(frame_bgr)
        det = Detection(
            bbox=BBoxXYXY(x1=0, y1=0, x2=int(w - 1), y2=int(h - 1)),
            confidence=1.0,
            class_id=0,
            class_name="full_frame",
        )

        decoded, _dec_metrics = decoder(frame_bgr, pre_gray, [det])

        out: list[dict] = []
        for d in decoded:
            out.append(
                {
                    "symbology": d.symbology,
                    "value": d.data,
                    "confidence": float(d.confidence),
                    "meta": {"bbox": d.bbox.model_dump(), **(d.meta or {})},
                }
            )
        return out
