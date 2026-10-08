import secrets
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import FormLockedError, JobNotFoundError, ProtectedCharacteristicError
from app.core.notices import AI_SCREENING_NOTICE, SCREENING_DISCLAIMER, privacy_notice
from app.models import Job, JobStatus, Recruiter
from app.repositories import jobs as jobs_repo
from app.repositories import phase_results as phase_results_repo
from app.schemas.forms import FormField, dump_form_fields, parse_form_fields
from app.schemas.jobs import (
    ApplicationCounts,
    ConditionKnockoutCount,
    FormWarningItem,
    JobCreate,
    JobDetailResponse,
    JobListItemResponse,
    JobResponse,
    JobUpdate,
    PublicJobResponse,
)
from app.services import conditions, guardrail
from app.services.screening import form_warnings

_SLUG_ATTEMPTS = 8


def public_apply_url(company_slug: str, slug: str) -> str:
    return f"{settings.PUBLIC_APP_URL.rstrip('/')}/{company_slug}/{slug}"


def _warnings(fields: list[FormField]) -> list[FormWarningItem]:
    """Soft warnings, plus guardrail hits on fields saved before the guardrail existed."""
    warnings = [
        FormWarningItem(field_id=item.field_id, message=item.message)
        for item in form_warnings(fields)
    ]
    warnings.extend(
        FormWarningItem(
            field_id=UUID(item.target),
            message=f"{item.message} It would be blocked if saved today. {item.suggestion}",
        )
        for item in guardrail.check_form_fields(fields)
    )
    return warnings


def _enforce_guardrail(requirements: str | None, fields: list[FormField] | None) -> None:
    violations = [
        *guardrail.check_requirements(requirements or ""),
        *guardrail.check_form_fields(fields or []),
    ]
    if violations:
        raise ProtectedCharacteristicError([item.dump() for item in violations])


def to_job_response(job: Job, recruiter: Recruiter) -> JobResponse:
    fields = parse_form_fields(job.form_fields)
    return JobResponse(
        id=job.id,
        title=job.title,
        description=job.description,
        requirements=job.requirements,
        form_fields=fields,
        form_warnings=_warnings(fields),
        company_slug=recruiter.company_slug,
        public_slug=job.public_slug,
        public_url=public_apply_url(recruiter.company_slug, job.public_slug),
        status=job.status,
        created_at=job.created_at,
        closed_at=job.closed_at,
    )


def public_form_fields(raw: object) -> list[FormField]:
    """Candidates never see knockout rules, answer weights or condition settings."""
    hidden = ("knockout", "scoring", "condition")
    return [
        field.model_copy(update={key: None for key in hidden if hasattr(field, key)})
        for field in parse_form_fields(raw)
    ]


def to_public_response(job: Job) -> PublicJobResponse:
    return PublicJobResponse(
        title=job.title,
        description=job.description,
        requirements=job.requirements,
        form_fields=public_form_fields(job.form_fields),
        before_you_apply=conditions.before_you_apply(parse_form_fields(job.form_fields)),
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
    _enforce_guardrail(data.requirements, data.form_fields)
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


async def _condition_knockouts(session: AsyncSession, job: Job) -> list[ConditionKnockoutCount]:
    counts = await phase_results_repo.count_knockouts_by_field(session, job.id)
    result: list[ConditionKnockoutCount] = []
    for field, _condition in conditions.must_conditions(parse_form_fields(job.form_fields)):
        stopped, moved_forward = counts.get(field.id, (0, 0))
        result.append(
            ConditionKnockoutCount(
                field_id=field.id, label=field.label, stopped=stopped, moved_forward=moved_forward
            )
        )
    return result


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
        condition_knockouts=await _condition_knockouts(session, job),
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
    _enforce_guardrail(data.requirements, data.form_fields)
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
