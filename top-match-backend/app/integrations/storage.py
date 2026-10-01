import asyncio
from pathlib import Path

from app.core.config import settings


def _root() -> Path:
    root = Path(settings.STORAGE_DIR)
    root.mkdir(parents=True, exist_ok=True)
    return root.resolve()


def _resolve(key: str) -> Path:
    path = (_root() / key).resolve()
    if not path.is_relative_to(_root()):
        raise ValueError("Invalid storage key")
    return path


def _put_sync(key: str, data: bytes) -> None:
    path = _resolve(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _get_sync(key: str) -> bytes:
    return _resolve(key).read_bytes()


def _delete_sync(key: str) -> None:
    _resolve(key).unlink(missing_ok=True)


def _exists_sync(key: str) -> bool:
    return _resolve(key).is_file()


async def put(key: str, data: bytes) -> None:
    await asyncio.to_thread(_put_sync, key, data)


async def get(key: str) -> bytes:
    return await asyncio.to_thread(_get_sync, key)


async def delete(key: str) -> None:
    await asyncio.to_thread(_delete_sync, key)


async def exists(key: str) -> bool:
    return await asyncio.to_thread(_exists_sync, key)
