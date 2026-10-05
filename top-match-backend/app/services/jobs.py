import secrets
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import FormLockedError, JobNotFoundError
from app.core.notices import AI_SCREENING_NOTICE, SCREENING_DISCLAIMER, privacy_notice
from app.models import Job, JobStatus, Recruiter
from app.repositories import jobs as jobs_repo
from app.schemas.forms import dump_form_fields, parse_form_fields
from app.schemas.jobs import (
    ApplicationCounts,
    JobCreate,
    JobDetailResponse,
    JobListItemResponse,
    JobResponse,
    JobUpdate,
    PublicJobResponse,
)

_SLUG_ATTEMPTS = 8


def public_apply_url(company_slug: str, slug: str) -> str:
    return f"{settings.PUBLIC_APP_URL.rstrip('/')}/{company_slug}/{slug}"


def to_job_response(job: Job, recruiter: Recruiter) -> JobResponse:
    return JobResponse(
        id=job.id,
        title=job.title,
        description=job.description,
        requirements=job.requirements,
        form_fields=parse_form_fields(job.form_fields),
        company_slug=recruiter.company_slug,
        public_slug=job.public_slug,
        public_url=public_apply_url(recruiter.company_slug, job.public_slug),
        status=job.status,
        created_at=job.created_at,
        closed_at=job.closed_at,
    )


def to_public_response(job: Job) -> PublicJobResponse:
    return PublicJobResponse(
        title=job.title,
        description=job.description,
        requirements=job.requirements,
        form_fields=parse_form_fields(job.form_fields),
        company_slug=job.recruiter.company_slug,
        status=job.status,
        privacy_notice=privacy_notice(),
        ai_screening_notice=AI_SCREENING_NOTICE,
        screening_disclaimer=SCREENING_DISCLAIMER,
    )


async def _unique_slug(session: AsyncSession) -> str:
    for _ in range(_SLUG_ATTEMPTS):
        slug = secrets.token_urlsafe(8)
        if await jobs_repo.get_by_slug(session, slug) is None:
            return slug
    raise RuntimeError("Could not generate a unique job slug")


async def get_owned_job(session: AsyncSession, job_id: UUID, recruiter_id: UUID) -> Job:
    job = await jobs_repo.get_by_id_and_recruiter(session, job_id, recruiter_id)
    if job is None:
        raise JobNotFoundError
    return job


async def create_job(session: AsyncSession, recruiter: Recruiter, data: JobCreate) -> Job:
    job = Job(
        recruiter_id=recruiter.id,
        title=data.title,
        description=data.description,
        requirements=data.requirements,
        form_fields=dump_form_fields(data.form_fields),
        public_slug=await _unique_slug(session),
        status=JobStatus.OPEN,
    )
    await jobs_repo.add(session, job)
    await session.commit()
    await session.refresh(job)
    return job


async def list_jobs(session: AsyncSession, recruiter_id: UUID) -> list[Job]:
    return await jobs_repo.list_for_recruiter(session, recruiter_id)


async def list_jobs_with_counts(
    session: AsyncSession, recruiter: Recruiter
) -> list[JobListItemResponse]:
    jobs = await list_jobs(session, recruiter.id)
    counts_by_job = await jobs_repo.count_applications_by_status_for_jobs(
        session, [job.id for job in jobs]
    )
    return [
        JobListItemResponse(
            **to_job_response(job, recruiter).model_dump(),
            application_counts=ApplicationCounts.from_status_map(counts_by_job[job.id]),
        )
        for job in jobs
    ]


async def get_job_detail(
    session: AsyncSession, job_id: UUID, recruiter: Recruiter
) -> JobDetailResponse:
    job = await get_owned_job(session, job_id, recruiter.id)
    counts = await jobs_repo.count_applications_by_status(session, job.id)
    return JobDetailResponse(
        **to_job_response(job, recruiter).model_dump(),
        application_counts=ApplicationCounts.from_status_map(counts),
        screening_disclaimer=SCREENING_DISCLAIMER,
        form_locked=await jobs_repo.has_applications(session, job.id),
    )


async def update_job(
    session: AsyncSession, job_id: UUID, recruiter_id: UUID, data: JobUpdate
) -> Job:
    job = await get_owned_job(session, job_id, recruiter_id)
    updates = data.model_dump(exclude_unset=True)
    if "form_fields" in updates:
        if await jobs_repo.has_applications(session, job.id):
            raise FormLockedError
        updates["form_fields"] = dump_form_fields(data.form_fields or [])
    for field, value in updates.items():
        setattr(job, field, value)
    await session.commit()
    await session.refresh(job)
    return job


async def close_job(session: AsyncSession, job_id: UUID, recruiter_id: UUID) -> Job:
    job = await get_owned_job(session, job_id, recruiter_id)
    if job.status != JobStatus.CLOSED:
        job.status = JobStatus.CLOSED
        job.closed_at = datetime.now(UTC)
        await session.commit()
        await session.refresh(job)
    return job


async def get_public_job(session: AsyncSession, slug: str) -> Job:
    job = await jobs_repo.get_by_slug(session, slug)
    if job is None:
        raise JobNotFoundError
    return job
