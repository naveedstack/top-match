"""Hands applications to the screening pipeline without blocking the request.

This is the only place work is queued. Step 3 replaces it with a Postgres-backed queue.
"""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from app.core.config import settings
from app.services.pipeline import process_application

logger = logging.getLogger(__name__)

_DRAIN_SECONDS = 30

_tasks: set[asyncio.Task[None]] = set()


async def _run(application_id: UUID, reclaim_processing: bool) -> None:
    try:
        await process_application(application_id, reclaim_processing=reclaim_processing)
    except Exception as exc:
        # Never log the exception text: it can carry resume content (Rule 4).
        logger.error(
            "screening task failed application_id=%s error=%s",
            application_id,
            type(exc).__name__,
        )


def enqueue_screening(application_id: UUID, *, reclaim_processing: bool = False) -> None:
    if not settings.PIPELINE_ENABLED:
        return
    task = asyncio.create_task(_run(application_id, reclaim_processing))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)


async def drain() -> None:
    """Give in-flight screening a chance to finish on shutdown; the stuck sweep covers the rest."""
    if _tasks:
        await asyncio.wait(set(_tasks), timeout=_DRAIN_SECONDS)
