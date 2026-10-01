import asyncio
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.email import normalize_email
from app.core.exceptions import (
    DuplicateApplicationError,
    JobClosedError,
    JobNotFoundError,
    ResumeAlreadyUsedError,
    ResumeNotFoundError,
)
from app.integrations import pdf as pdf_lib
from app.integrations import storage
from app.models import Application, ApplicationStatus, JobStatus
from app.repositories import applications as applications_repo
from app.repositories import jobs as jobs_repo


def resume_storage_key(file_id: UUID) -> str:
    return f"{file_id}.pdf"


async def store_resume(pdf_bytes: bytes) -> UUID:
    await asyncio.to_thread(pdf_lib.validate_pdf, pdf_bytes)
    file_id = uuid4()
    await storage.put(resume_storage_key(file_id), pdf_bytes)
    return file_id


async def apply_to_job(session: AsyncSession, slug: str, email: str, file_id: UUID) -> Application:
    job = await jobs_repo.get_by_slug(session, slug)
    if job is None:
        raise JobNotFoundError
    if job.status != JobStatus.OPEN:
        raise JobClosedError

    storage_key = resume_storage_key(file_id)
    if not await storage.exists(storage_key):
        raise ResumeNotFoundError
    if await applications_repo.get_by_storage_key(session, storage_key) is not None:
        raise ResumeAlreadyUsedError

    normalized = normalize_email(str(email))
    existing = await applications_repo.get_by_job_and_email(session, job.id, normalized)
    if existing is not None:
        raise DuplicateApplicationError

    application = Application(
        job_id=job.id,
        email=normalized,
        status=ApplicationStatus.RECEIVED,
        resume_storage_key=storage_key,
        extracted_text=None,
    )
    try:
        await applications_repo.add(session, application)
        await session.commit()
        await session.refresh(application)
    except IntegrityError:
        await session.rollback()
        raise DuplicateApplicationError from None
    return application
