from __future__ import annotations

from functools import lru_cache

import boto3
import anyio
from botocore.client import Config
from botocore.exceptions import ClientError

from app.core.config import settings


@lru_cache(maxsize=1)
def _client():
    return boto3.client(
        "s3",
        region_name=settings.S3_REGION,
        endpoint_url=settings.S3_ENDPOINT_URL,
        aws_access_key_id=settings.S3_ACCESS_KEY_ID,
        aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
        config=Config(signature_version="s3v4"),
    )


class S3Service:
    def presign_put_url(self, *, object_key: str, content_type: str, expires_in: int | None = None) -> str:
        s3 = _client()
        return s3.generate_presigned_url(
            "put_object",
            Params={"Bucket": settings.S3_BUCKET, "Key": object_key, "ContentType": content_type},
            ExpiresIn=expires_in if expires_in is not None else settings.S3_PRESIGN_EXPIRES_SECONDS,
        )

    def presign_get_url(self, *, object_key: str, expires_in: int | None = None) -> str:
        """
        Presign a GET URL for downloading an object.

        Used by the dashboard for downloading report outputs (and any other
        evidence objects) without proxying the file through the API server.
        """
        s3 = _client()
        return s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_BUCKET, "Key": object_key},
            ExpiresIn=expires_in if expires_in is not None else settings.S3_PRESIGN_EXPIRES_SECONDS,
        )

    def head_object(self, *, object_key: str) -> dict[str, object] | None:
        s3 = _client()
        try:
            res = s3.head_object(Bucket=settings.S3_BUCKET, Key=object_key)
        except ClientError as exc:
            code = str(exc.response.get("Error", {}).get("Code") or "")
            if code in {"404", "NoSuchKey", "NotFound"}:
                return None
            raise
        etag = res.get("ETag")
        if isinstance(etag, str):
            etag = etag.strip('"')
        return {
            "etag": etag,
            "bytes": res.get("ContentLength"),
            "content_type": res.get("ContentType"),
        }

    async def head_object_async(self, *, object_key: str) -> dict[str, object] | None:
        """
        Async wrapper for `head_object`.

        boto3 is synchronous and will block the event loop if called directly from async endpoints.
        """
        return await anyio.to_thread.run_sync(lambda: self.head_object(object_key=object_key))

    def delete_object(self, *, object_key: str) -> bool:
        s3 = _client()
        try:
            s3.delete_object(Bucket=settings.S3_BUCKET, Key=object_key)
        except ClientError as exc:
            code = str(exc.response.get("Error", {}).get("Code") or "")
            if code in {"404", "NoSuchKey", "NotFound"}:
                return False
            raise
        return True

    async def delete_object_async(self, *, object_key: str) -> bool:
        return await anyio.to_thread.run_sync(lambda: self.delete_object(object_key=object_key))

