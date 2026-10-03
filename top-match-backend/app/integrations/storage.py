from __future__ import annotations

import asyncio
import inspect
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import aioboto3
from botocore.exceptions import ClientError

from app.core.config import settings
from app.core.exceptions import InvalidResumeError, ResumeTooLargeError

_SSE_ALGORITHM = "AES256"
_PENDING_SUFFIX = ".pending"


@dataclass(frozen=True)
class PresignedPut:
    url: str
    headers: dict[str, str]
    expires_at: datetime


@dataclass(frozen=True)
class ObjectHead:
    content_length: int
    content_type: str | None


def _is_s3() -> bool:
    return settings.STORAGE_BACKEND == "s3"


def _object_key(key: str) -> str:
    prefix = settings.S3_PREFIX.strip("/")
    if prefix:
        return f"{prefix}/{key}"
    return key


def _expires_at() -> datetime:
    return datetime.now(UTC) + timedelta(seconds=settings.S3_UPLOAD_URL_SECONDS)


def _root() -> Path:
    root = Path(settings.STORAGE_DIR)
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def _resolve(key: str) -> Path:
    path = (_root() / key).resolve()
    if not path.is_relative_to(_root()):
        raise ValueError("Invalid storage key")
    return path


def _pending_path(key: str) -> Path:
    return _resolve(f"{key}{_PENDING_SUFFIX}")


def _put_sync(key: str, data: bytes) -> None:
    path = _resolve(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _get_sync(key: str) -> bytes:
    return _resolve(key).read_bytes()


def _delete_sync(key: str) -> None:
    path = _resolve(key)
    path.unlink(missing_ok=True)
    _pending_path(key).unlink(missing_ok=True)


def _exists_sync(key: str) -> bool:
    return _resolve(key).is_file()


def _head_sync(key: str) -> ObjectHead | None:
    path = _resolve(key)
    if not path.is_file():
        return None
    return ObjectHead(content_length=path.stat().st_size, content_type="application/pdf")


def _write_pending_sync(key: str, content_type: str, byte_size: int) -> None:
    path = _pending_path(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"content_type": content_type, "byte_size": byte_size}),
        encoding="utf-8",
    )


def _read_pending_sync(key: str) -> dict[str, Any] | None:
    path = _pending_path(key)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def _s3_session() -> aioboto3.Session:
    access_key = settings.AWS_ACCESS_KEY_ID.strip()
    secret = settings.AWS_SECRET_ACCESS_KEY
    if access_key and secret is not None:
        return aioboto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret.get_secret_value(),
        )
    return aioboto3.Session()


@asynccontextmanager
async def _s3_client() -> AsyncIterator[Any]:
    async with _s3_session().client("s3", region_name=settings.S3_REGION) as client:
        yield client


def _s3_missing(exc: ClientError) -> bool:
    code = exc.response.get("Error", {}).get("Code")
    return code in {"404", "NoSuchKey", "NotFound"}


async def presign_put(
    key: str,
    *,
    content_type: str,
    byte_size: int,
    put_url: str,
) -> PresignedPut:
    expires_at = _expires_at()
    if not _is_s3():
        await asyncio.to_thread(_write_pending_sync, key, content_type, byte_size)
        return PresignedPut(
            url=put_url,
            headers={"Content-Type": content_type},
            expires_at=expires_at,
        )

    params: dict[str, Any] = {
        "Bucket": settings.S3_BUCKET,
        "Key": _object_key(key),
        "ContentType": content_type,
        "ContentLength": byte_size,
        "ServerSideEncryption": _SSE_ALGORITHM,
    }
    async with _s3_client() as client:
        generated: Any = client.generate_presigned_url(
            "put_object",
            Params=params,
            ExpiresIn=settings.S3_UPLOAD_URL_SECONDS,
        )
        if inspect.isawaitable(generated):
            generated = await generated
    if not isinstance(generated, str):
        raise RuntimeError("presign did not return a URL")
    return PresignedPut(
        url=generated,
        headers={
            "Content-Type": content_type,
            "x-amz-server-side-encryption": _SSE_ALGORITHM,
        },
        expires_at=expires_at,
    )


async def receive_local_put(key: str, data: bytes, content_type: str) -> None:
    if _is_s3():
        raise FileNotFoundError
    pending = await asyncio.to_thread(_read_pending_sync, key)
    if pending is None:
        raise FileNotFoundError
    expected_type = pending.get("content_type")
    expected_size = pending.get("byte_size")
    if expected_type != content_type:
        raise InvalidResumeError("File is not a PDF")
    if not isinstance(expected_size, int) or expected_size < 1:
        raise InvalidResumeError("File is empty")
    if not data:
        raise InvalidResumeError("File is empty")
    if len(data) != expected_size:
        if len(data) > expected_size:
            raise ResumeTooLargeError
        raise InvalidResumeError("File is not a PDF")
    await put(key, data)


async def put(key: str, data: bytes) -> None:
    if not _is_s3():
        await asyncio.to_thread(_put_sync, key, data)
        return
    async with _s3_client() as client:
        await client.put_object(
            Bucket=settings.S3_BUCKET,
            Key=_object_key(key),
            Body=data,
            ContentType="application/pdf",
            ServerSideEncryption=_SSE_ALGORITHM,
        )


async def get(key: str) -> bytes:
    if not _is_s3():
        return await asyncio.to_thread(_get_sync, key)
    async with _s3_client() as client:
        response = await client.get_object(Bucket=settings.S3_BUCKET, Key=_object_key(key))
        body = response["Body"]
        payload = await body.read()
        if not isinstance(payload, (bytes, bytearray)):
            raise TypeError("S3 object body was not bytes")
        return bytes(payload)


async def delete(key: str) -> None:
    if not _is_s3():
        await asyncio.to_thread(_delete_sync, key)
        return
    async with _s3_client() as client:
        await client.delete_object(Bucket=settings.S3_BUCKET, Key=_object_key(key))


async def exists(key: str) -> bool:
    return await head(key) is not None


async def head(key: str) -> ObjectHead | None:
    if not _is_s3():
        return await asyncio.to_thread(_head_sync, key)
    try:
        async with _s3_client() as client:
            response = await client.head_object(Bucket=settings.S3_BUCKET, Key=_object_key(key))
    except ClientError as exc:
        if _s3_missing(exc):
            return None
        raise
    content_length = response.get("ContentLength")
    if not isinstance(content_length, int):
        return None
    content_type = response.get("ContentType")
    return ObjectHead(
        content_length=content_length,
        content_type=content_type if isinstance(content_type, str) else None,
    )
