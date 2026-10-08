from __future__ import annotations

import csv
import io
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ApplicationNotFoundError
from app.core.notices import SCREENING_DISCLAIMER
from app.models import Application, ExportEvent, PhaseOutcome, Recruiter, ScreeningPhase
from app.repositories import applications as applications_repo
from app.repositories import exports as exports_repo
from app.schemas.applications import ExportRequest
from app.schemas.conditions import ConditionImportance
from app.schemas.forms import FormField, condition_of, parse_form_fields
from app.services import conditions
from app.services import jobs as jobs_service

_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")
_CSV_HEADER = [
    "rank",
    "email",
    "score",
    "key strengths",
    "missing requirements",
    "applied at",
    "stopped at",
    "reason",
    "stopped by condition",
]
_IMPORTANCE_LABEL: dict[ConditionImportance, str] = {
    "must": "Must",
    "preferred": "Preferred",
    "info": "Info only",
}


def escape_csv_cell(value: object) -> str:
    text = "" if value is None else str(value)
    if text[:1] in _FORMULA_PREFIXES:
        return f"'{text}"
    return text


def _join(values: list[str]) -> str:
    return "; ".join(values)


def _column_label(field: FormField) -> str:
    condition = condition_of(field)
    if condition is None:
        return field.label
    return f"{field.label} ({_IMPORTANCE_LABEL[condition.importance]})"


def _stopping_conditions(application: Application, fields: list[FormField]) -> list[str]:
    """Conditions that knocked the application out, if it is still stopped at knockout."""
    if application.stopped_phase != ScreeningPhase.KNOCKOUT:
        return []
    for result in reversed(application.phase_results):
        if result.phase == ScreeningPhase.KNOCKOUT and result.outcome == PhaseOutcome.FAIL:
            return conditions.failed_condition_labels(fields, result.reasons)
    return []


def render_csv(rows: list[tuple[int, Application]], form_fields: object | None = None) -> str:
    fields = parse_form_fields(form_fields)
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow([escape_csv_cell(SCREENING_DISCLAIMER)])
    writer.writerow(_CSV_HEADER + [escape_csv_cell(_column_label(field)) for field in fields])
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
                escape_csv_cell(
                    "" if application.stopped_phase is None else application.stopped_phase.value
                ),
                escape_csv_cell(application.stop_reason),
                escape_csv_cell(_join(_stopping_conditions(application, fields))),
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
