from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    AttachmentAlreadyUsedError,
    AttachmentNotFoundError,
    FormAnswersError,
    InvalidAttachmentError,
)
from app.models import Job
from app.schemas.forms import (
    CheckboxesFormField,
    FormField,
    NumberFormField,
    TextFormField,
    parse_form_fields,
)
from app.services.attachments import PreparedAttachment, load_prepared


def _missing(field: FormField, answers: dict[str, Any], field_id: str) -> bool:
    if field_id not in answers:
        return True
    value = answers[field_id]
    if field.type == "text":
        return not isinstance(value, str) or not value.strip()
    if field.type == "checkboxes":
        return not isinstance(value, list) or len(value) == 0
    if field.type == "file":
        return value is None or value == ""
    if field.type == "number":
        return value is None or value == ""
    return not isinstance(value, str) or not value.strip()


def _validate_text(field: TextFormField, value: object) -> str | None:
    if not isinstance(value, str):
        return "Must be text"
    stripped = value.strip()
    if len(stripped) > field.max_length:
        return f"Must be at most {field.max_length} characters"
    return None


def _validate_number(field: NumberFormField, value: object) -> str | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return "Must be a number"
    number = float(value)
    if field.integer_only and not number.is_integer():
        return "Must be a whole number"
    if field.min is not None and number < field.min:
        return f"Must be at least {field.min}"
    if field.max is not None and number > field.max:
        return f"Must be at most {field.max}"
    return None


def _validate_choice(options: list[str], value: object) -> str | None:
    if not isinstance(value, str) or value not in options:
        return "Select a valid option"
    return None


def _validate_checkboxes(field: CheckboxesFormField, value: object) -> str | None:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        return "Select valid options"
    unique: list[str] = []
    seen: set[str] = set()
    for item in value:
        if item not in field.options:
            return "Select valid options"
        if item in seen:
            continue
        seen.add(item)
        unique.append(item)
    if not unique:
        return "Select valid options"
    return None


async def validate_answers(
    session: AsyncSession,
    job: Job,
    answers: dict[str, Any],
) -> tuple[dict[str, Any], list[PreparedAttachment]]:
    fields = parse_form_fields(job.form_fields)
    known = {str(field.id) for field in fields}
    errors: dict[str, str] = {}
    cleaned: dict[str, Any] = {}
    attachments: list[PreparedAttachment] = []
    seen_files: set[UUID] = set()

    for key in answers:
        if key not in known:
            errors[key] = "Unknown field"

    for field in fields:
        field_id = str(field.id)
        missing = _missing(field, answers, field_id)
        if field.required and missing:
            errors[field_id] = "This field is required"
            continue
        if missing:
            continue
        value = answers[field_id]
        if field.type == "text":
            message = _validate_text(field, value)
            if message:
                errors[field_id] = message
            else:
                cleaned[field_id] = str(value).strip()
        elif field.type == "number":
            message = _validate_number(field, value)
            if message:
                errors[field_id] = message
            else:
                number = float(value)
                cleaned[field_id] = int(number) if field.integer_only else number
        elif field.type in {"dropdown", "radio"}:
            message = _validate_choice(field.options, value)
            if message:
                errors[field_id] = message
            else:
                cleaned[field_id] = value
        elif field.type == "checkboxes":
            message = _validate_checkboxes(field, value)
            if message:
                errors[field_id] = message
            else:
                unique: list[str] = []
                seen: set[str] = set()
                if isinstance(value, list):
                    for item in value:
                        if isinstance(item, str) and item not in seen:
                            seen.add(item)
                            unique.append(item)
                cleaned[field_id] = unique
        elif field.type == "file":
            try:
                file_id = UUID(str(value))
            except ValueError, TypeError:
                errors[field_id] = "Upload a valid file"
                continue
            if file_id in seen_files:
                errors[field_id] = "This file was already used"
                continue
            try:
                prepared = await load_prepared(
                    session,
                    file_id,
                    job_id=job.id,
                    field_id=field.id,
                    accept=field.accept,
                )
            except AttachmentNotFoundError:
                errors[field_id] = "Upload a file"
            except AttachmentAlreadyUsedError:
                errors[field_id] = "This file was already used"
            except InvalidAttachmentError as exc:
                errors[field_id] = exc.message
            else:
                seen_files.add(file_id)
                attachments.append(prepared)
                cleaned[field_id] = str(file_id)

    if errors:
        raise FormAnswersError(errors)
    return cleaned, attachments
