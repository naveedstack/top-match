from __future__ import annotations

import csv
import io
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ApplicationNotFoundError
from app.core.notices import SCREENING_DISCLAIMER
from app.models import Application, ExportEvent, Recruiter
from app.repositories import applications as applications_repo
from app.repositories import exports as exports_repo
from app.schemas.applications import ExportRequest
from app.schemas.forms import parse_form_fields
from app.services import jobs as jobs_service

_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")
_CSV_HEADER = ["rank", "email", "score", "key strengths", "missing requirements", "applied at"]


def escape_csv_cell(value: object) -> str:
    text = "" if value is None else str(value)
    if text[:1] in _FORMULA_PREFIXES:
        return f"'{text}"
    return text


def _join(values: list[str]) -> str:
    return "; ".join(values)


def render_csv(rows: list[tuple[int, Application]], form_fields: object | None = None) -> str:
    fields = parse_form_fields(form_fields)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([escape_csv_cell(SCREENING_DISCLAIMER)])
    writer.writerow(_CSV_HEADER + [escape_csv_cell(field.label) for field in fields])
    for rank, application in rows:
        evaluation = application.evaluation
        strengths = [] if evaluation is None else list(evaluation.key_strengths)
        missing = [] if evaluation is None else list(evaluation.missing_requirements)
        stored = application.answers or {}
        attachments_by_field = {item.field_id: item for item in application.attachments}
        extra: list[str] = []
        for field in fields:
            if field.type == "file":
                attachment = attachments_by_field.get(field.id)
                extra.append("" if attachment is None else attachment.filename)
                continue
            raw = stored.get(str(field.id))
            if raw is None:
                extra.append("")
            elif isinstance(raw, list):
                extra.append(", ".join(str(item) for item in raw))
            else:
                extra.append(str(raw))
        writer.writerow(
            [
                escape_csv_cell(rank),
                escape_csv_cell(application.email),
                escape_csv_cell(application.score),
                escape_csv_cell(_join(strengths)),
                escape_csv_cell(_join(missing)),
                escape_csv_cell(application.created_at.isoformat()),
                *[escape_csv_cell(item) for item in extra],
            ]
        )
    return buffer.getvalue()


async def export_job(
    session: AsyncSession, job_id: UUID, recruiter: Recruiter, body: ExportRequest
) -> tuple[str, list[UUID]]:
    job = await jobs_service.get_owned_job(session, job_id, recruiter.id)
    ids = list(dict.fromkeys(body.application_ids)) if body.application_ids else None
    applications = await applications_repo.list_for_export(session, job.id, ids, body.top_n)
    if ids is not None and {row.id for row in applications} != set(ids):
        raise ApplicationNotFoundError
    ranked = list(enumerate(applications, start=1))
    exported_ids = [application.id for application in applications]
    event = ExportEvent(
        recruiter_id=recruiter.id,
        job_id=job.id,
        application_ids=[str(item) for item in exported_ids],
    )
    await exports_repo.add(session, event)
    await session.commit()
    return render_csv(ranked, job.form_fields), exported_ids
