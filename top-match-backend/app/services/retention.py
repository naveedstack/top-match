from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import SessionLocal
from app.integrations import storage
from app.repositories import applications as applications_repo
from app.services import attachments as attachments_service

logger = logging.getLogger(__name__)


async def purge_expired_applications(session: AsyncSession | None = None) -> dict[str, int]:
    cutoff = datetime.now(UTC) - timedelta(days=settings.RETENTION_DAYS)

    async def _run(active: AsyncSession) -> dict[str, int]:
        rows = await applications_repo.list_expired_for_purge(active, cutoff)
        purged = 0
        storage_missing = 0
        for application in rows:
            for attachment in application.attachments:
                try:
                    await attachments_service.delete_storage(attachment)
                except OSError:
                    logger.exception("retention attachment delete failed")
                    storage_missing += 1
            key = application.resume_storage_key
            if key is None or not await storage.exists(key):
                storage_missing += 1
            else:
                try:
                    await storage.delete(key)
                except OSError:
                    logger.exception("retention storage delete failed")
                    storage_missing += 1
            await active.delete(application)
            purged += 1
        if purged:
            await active.commit()
        logger.info(
            "retention purge complete purged=%s storage_missing=%s",
            purged,
            storage_missing,
        )
        return {"purged": purged, "storage_missing": storage_missing}

    if session is not None:
        return await _run(session)
    async with SessionLocal() as owned:
        return await _run(owned)
