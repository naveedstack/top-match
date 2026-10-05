import asyncio
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.email import normalize_email
from app.core.exceptions import (
    ApplicationNotFoundError,
    DuplicateApplicationError,
    InvalidResumeError,
    InvalidTokenError,
    JobClosedError,
    JobNotFoundError,
    ResumeAlreadyUsedError,
    ResumeNotFoundError,
    ResumeTooLargeError,
)
from app.core.notices import SCREENING_DISCLAIMER
from app.core.security import create_resume_token, decode_resume_token
from app.integrations import pdf as pdf_lib
from app.integrations import storage
from app.models import Application, ApplicationAttachment, ApplicationStatus, JobStatus, Recruiter
from app.repositories import applications as applications_repo
from app.repositories import jobs as jobs_repo
from app.schemas.applications import (
    ApplicationAnswerItem,
    ApplicationDetailResponse,
    LeaderboardItem,
    LeaderboardResponse,
)
from app.schemas.evaluation import Citation
from app.schemas.forms import parse_form_fields
from app.schemas.jobs import ApplicationCounts
from app.services import attachments as attachments_service
from app.services import jobs as jobs_service
from app.services.forms import validate_answers
from app.services.pipeline import rescore_application as run_rescore


def resume_storage_key(file_id: UUID) -> str:
    return f"{file_id}.pdf"


def resume_url_for(application_id: UUID) -> str:
    token = create_resume_token(application_id)
    return f"{settings.API_V1_STR}/public/resumes/{token}"


async def request_upload_url(
    file_id: UUID,
    *,
    content_type: str,
    byte_size: int,
    put_url: str,
) -> storage.PresignedPut:
    normalized_type = content_type.split(";")[0].strip().lower()
    if normalized_type != "application/pdf":
        raise InvalidResumeError("File is not a PDF")
    if byte_size > settings.MAX_UPLOAD_BYTES:
        raise ResumeTooLargeError
    return await storage.presign_put(
        resume_storage_key(file_id),
        content_type="application/pdf",
        byte_size=byte_size,
        put_url=put_url,
    )


async def store_local_put(file_id: UUID, pdf_bytes: bytes, content_type: str) -> None:
    normalized_type = content_type.split(";")[0].strip().lower()
    if normalized_type != "application/pdf":
        raise InvalidResumeError("File is not a PDF")
    if len(pdf_bytes) > settings.MAX_UPLOAD_BYTES:
        raise ResumeTooLargeError
    try:
        await storage.receive_local_put(
            resume_storage_key(file_id),
            pdf_bytes,
            "application/pdf",
        )
    except FileNotFoundError as exc:
        raise ResumeNotFoundError from exc


async def confirm_resume(file_id: UUID) -> UUID:
    key = resume_storage_key(file_id)
    meta = await storage.head(key)
    if meta is None:
        raise ResumeNotFoundError
    if meta.content_length > settings.MAX_UPLOAD_BYTES:
        await storage.delete(key)
        raise ResumeTooLargeError
    try:
        pdf_bytes = await storage.get(key)
        await asyncio.to_thread(pdf_lib.validate_pdf, pdf_bytes)
    except InvalidResumeError:
        await storage.delete(key)
        raise
    except OSError, ValueError:
        await storage.delete(key)
        raise InvalidResumeError("File is not a PDF") from None
    return file_id


async def apply_to_job(
    session: AsyncSession,
    slug: str,
    email: str,
    file_id: UUID,
    answers: dict[str, Any] | None = None,
) -> Application:
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

    cleaned_answers, attachments = await validate_answers(session, job, answers or {})

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
        consented_at=datetime.now(UTC),
        answers=cleaned_answers,
    )
    try:
        await applications_repo.add(session, application)
        for prepared in attachments:
            session.add(
                ApplicationAttachment(
                    application_id=application.id,
                    field_id=prepared.field_id,
                    storage_key=prepared.storage_key,
                    filename=prepared.filename,
                    content_type=prepared.content_type,
                    byte_size=prepared.byte_size,
                )
            )
        await session.commit()
        await session.refresh(application)
    except IntegrityError:
        await session.rollback()
        raise DuplicateApplicationError from None
    return application


async def get_leaderboard(
    session: AsyncSession,
    job_id: UUID,
    recruiter_id: UUID,
    *,
    status: ApplicationStatus | None,
    limit: int,
    offset: int,
) -> LeaderboardResponse:
    job = await jobs_service.get_owned_job(session, job_id, recruiter_id)
    rows = await applications_repo.list_for_leaderboard(
        session, job.id, status=status, limit=limit, offset=offset
    )
    total = await applications_repo.count_for_leaderboard(session, job.id, status=status)
    counts = await jobs_repo.count_applications_by_status(session, job.id)
    return LeaderboardResponse(
        items=[
            LeaderboardItem(
                id=application.id,
                email=application.email,
                status=application.status,
                score=application.score,
                needs_review=needs_review,
                created_at=application.created_at,
            )
            for application, needs_review in rows
        ],
        counts=ApplicationCounts.from_status_map(counts),
        total=total,
        screening_disclaimer=SCREENING_DISCLAIMER,
    )


def to_detail(application: Application) -> ApplicationDetailResponse:
    evaluation = application.evaluation
    attachments_by_field = {item.field_id: item for item in application.attachments}
    stored = application.answers or {}
    answers: list[ApplicationAnswerItem] = []
    for field in parse_form_fields(application.job.form_fields):
        raw = stored.get(str(field.id))
        if field.type == "file":
            attachment = attachments_by_field.get(field.id)
            answers.append(
                ApplicationAnswerItem(
                    field_id=field.id,
                    label=field.label,
                    type="file",
                    value=None if attachment is None else attachment.filename,
                    filename=None if attachment is None else attachment.filename,
                    download_url=(
                        None
                        if attachment is None
                        else attachments_service.attachment_url_for(attachment.id)
                    ),
                )
            )
            continue
        value: str | float | list[str] | None
        if raw is None:
            value = None
        elif field.type == "checkboxes":
            value = [item for item in raw if isinstance(item, str)] if isinstance(raw, list) else []
        elif field.type == "number" and isinstance(raw, (int, float)) and not isinstance(raw, bool):
            value = float(raw)
        elif isinstance(raw, str):
            value = raw
        else:
            value = None
        answers.append(
            ApplicationAnswerItem(
                field_id=field.id,
                label=field.label,
                type=field.type,
                value=value,
            )
        )
    return ApplicationDetailResponse(
        id=application.id,
        email=application.email,
        status=application.status,
        score=application.score,
        created_at=application.created_at,
        is_resume=None if evaluation is None else evaluation.is_resume,
        refusal_reason=None if evaluation is None else evaluation.refusal_reason,
        key_strengths=[] if evaluation is None else list(evaluation.key_strengths),
        missing_requirements=[] if evaluation is None else list(evaluation.missing_requirements),
        citations=(
            []
            if evaluation is None
            else [Citation.model_validate(item) for item in evaluation.citations]
        ),
        injection_suspected=None if evaluation is None else evaluation.injection_suspected,
        needs_review=None if evaluation is None else evaluation.needs_review,
        resume_url=resume_url_for(application.id) if application.resume_storage_key else None,
        answers=answers,
    )


async def get_owned_detail(
    session: AsyncSession, application_id: UUID, recruiter_id: UUID
) -> ApplicationDetailResponse:
    application = await applications_repo.get_by_id_and_recruiter(
        session, application_id, recruiter_id
    )
    if application is None:
        raise ApplicationNotFoundError
    return to_detail(application)


async def rescore(session: AsyncSession, application_id: UUID, recruiter: Recruiter) -> Application:
    return await run_rescore(session, application_id, recruiter.id)


async def get_resume_pdf(session: AsyncSession, token: str) -> bytes:
    application_id = decode_resume_token(token)
    application = await applications_repo.get_by_id(session, application_id)
    if application is None or application.resume_storage_key is None:
        raise InvalidTokenError
    if not await storage.exists(application.resume_storage_key):
        raise ResumeNotFoundError
    return await storage.get(application.resume_storage_key)
