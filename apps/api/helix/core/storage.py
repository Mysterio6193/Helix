"""S3-compatible storage layer (works with MinIO and AWS S3)."""
from __future__ import annotations

from typing import BinaryIO
from uuid import uuid4

import boto3
from botocore.client import Config

from helix.core.config import settings


class S3Storage:
    def __init__(self) -> None:
        self.bucket = settings.s3_bucket
        self.client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint,
            region_name=settings.s3_region,
            aws_access_key_id=settings.s3_access_key,
            aws_secret_access_key=settings.s3_secret_key,
            config=Config(signature_version="s3v4"),
        )

    def ensure_bucket(self) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except Exception:
            self.client.create_bucket(Bucket=self.bucket)

    def put_bytes(
        self,
        key: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )
        return key

    def put_stream(self, key: str, stream: BinaryIO, content_type: str) -> str:
        self.client.upload_fileobj(
            stream,
            self.bucket,
            key,
            ExtraArgs={"ContentType": content_type},
        )
        return key

    def presign_get(self, key: str, ttl_seconds: int = 3600) -> str:
        return self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket, "Key": key},
            ExpiresIn=ttl_seconds,
        )

    def make_key(self, prefix: str, ext: str) -> str:
        return f"{prefix}/{uuid4()}.{ext.lstrip('.')}"


_storage: S3Storage | None = None


def get_storage() -> S3Storage:
    global _storage
    if _storage is None:
        _storage = S3Storage()
    return _storage
