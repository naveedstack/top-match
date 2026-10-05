from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import (
    ApplicationNotFoundError,
    EvaluationFailedError,
    InvalidResumeError,
)
from app.db.session import SessionLocal
from app.integrations import storage
from app.integrations.llm import EvaluationCompleter
from app.models import Application, ApplicationStatus
from app.repositories import applications as applications_repo
from app.repositories import evaluations as evaluations_repo
from app.services import evaluation as evaluation_service
from app.services.ingestion import IngestionResult, extract_text

logger = logging.getLogger(__name__)

_llm_semaphore: asyncio.Semaphore | None = None


def _semaphore() -> asyncio.Semaphore:
    global _llm_semaphore
    if _llm_semaphore is None:
        _llm_semaphore = asyncio.Semaphore(settings.LLM_MAX_CONCURRENCY)
    return _llm_semaphore


async def _mark_failed(session: AsyncSession, application: Application) -> None:
    application.status = ApplicationStatus.FAILED
    application.score = None
    await session.commit()


async def _prepare_storage_key(
    session: AsyncSession,
    application_id: UUID,
    *,
    reclaim_processing: bool,
) -> str | None:
    claimed = await applications_repo.claim_for_processing(
        session, application_id, reclaim_processing=reclaim_processing
    )
    if not claimed:
        return None
    application = await applications_repo.get_by_id(session, application_id, populate_existing=True)
    if application is None or application.job is None:
        return None
    storage_key = application.resume_storage_key
    if storage_key is None or not await storage.exists(storage_key):
        await _mark_failed(session, application)
        return None
    return storage_key


async def _ingest(storage_key: str) -> IngestionResult:
    pdf_bytes = await storage.get(storage_key)
    return await extract_text(pdf_bytes)


async def _finalize(
    session: AsyncSession,
    application: Application,
    ingestion: IngestionResult,
    completer: EvaluationCompleter | None,
) -> None:
    job = application.job
    if job is None:
        await _mark_failed(session, application)
        return
    application.extracted_text = ingestion.text
    await session.commit()
    try:
        async with _semaphore():
            result = await evaluation_service.evaluate(job, ingestion.text, completer=completer)
    except EvaluationFailedError:
        logger.exception("application processing failed during evaluation")
        await _mark_failed(session, application)
        return
    await evaluations_repo.delete_by_application_id(session, application.id)
    await evaluation_service.save_evaluation(session, application.id, result, commit=False)
    application.status = ApplicationStatus.SCORED if result.is_resume else ApplicationStatus.REFUSED
    application.score = result.score
    await session.commit()


async def _mark_failed_by_id(application_id: UUID) -> None:
    async with SessionLocal() as owned:
        application = await applications_repo.get_by_id(
            owned, application_id, populate_existing=True
        )
        if application is not None:
            await _mark_failed(owned, application)


async def _process(
    session: AsyncSession,
    application_id: UUID,
    *,
    reclaim_processing: bool,
    completer: EvaluationCompleter | None,
) -> None:
    storage_key = await _prepare_storage_key(
        session, application_id, reclaim_processing=reclaim_processing
    )
    if storage_key is None:
        return
    try:
        ingestion = await _ingest(storage_key)
    except InvalidResumeError, OSError, ValueError:
        logger.exception("application processing failed during ingestion")
        await _mark_failed_after_prepare(session, application_id)
        return
    application = await applications_repo.get_by_id(session, application_id, populate_existing=True)
    if application is None or application.job is None:
        return
    await _finalize(session, application, ingestion, completer)


async def _mark_failed_after_prepare(session: AsyncSession, application_id: UUID) -> None:
    application = await applications_repo.get_by_id(session, application_id, populate_existing=True)
    if application is not None:
        await _mark_failed(session, application)


async def process_application(
    application_id: UUID,
    session: AsyncSession | None = None,
    *,
    reclaim_processing: bool = False,
    completer: EvaluationCompleter | None = None,
) -> None:
    if session is not None:
        await _process(
            session,
            application_id,
            reclaim_processing=reclaim_processing,
            completer=completer,
        )
        return
    storage_key: str | None = None
    async with SessionLocal() as owned:
        storage_key = await _prepare_storage_key(
            owned, application_id, reclaim_processing=reclaim_processing
        )
    if storage_key is None:
        return
    try:
        ingestion = await _ingest(storage_key)
    except InvalidResumeError, OSError, ValueError:
        logger.exception("application processing failed during ingestion")
        await _mark_failed_by_id(application_id)
        return
    async with SessionLocal() as owned:
        application = await applications_repo.get_by_id(
            owned, application_id, populate_existing=True
        )
        if application is None or application.job is None:
            return
        await _finalize(owned, application, ingestion, completer)


async def recover_stuck_applications(
    session: AsyncSession | None = None,
    *,
    completer: EvaluationCompleter | None = None,
) -> list[UUID]:
    cutoff = datetime.now(UTC) - timedelta(minutes=settings.STUCK_APPLICATION_MINUTES)

    async def _run(active: AsyncSession) -> list[UUID]:
        ids = await applications_repo.list_stuck_ids(active, cutoff)
        for application_id in ids:
            await process_application(
                application_id,
                active,
                reclaim_processing=True,
                completer=completer,
            )
        return ids

    if session is not None:
        return await _run(session)
    async with SessionLocal() as owned:
        return await _run(owned)


async def rescore_application(
    session: AsyncSession,
    application_id: UUID,
    recruiter_id: UUID,
) -> Application:
    application = await applications_repo.get_by_id_and_recruiter(
        session, application_id, recruiter_id
    )
    if application is None or application.status != ApplicationStatus.FAILED:
        raise ApplicationNotFoundError
    application.status = ApplicationStatus.PROCESSING
    await session.commit()
    return application
