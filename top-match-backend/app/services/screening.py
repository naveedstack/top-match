"""Code-only screening checks. Nothing here calls the model."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, TypeGuard
from uuid import UUID

from app.schemas.forms import (
    CheckboxesFormField,
    DropdownFormField,
    FormField,
    NumberFormField,
    RadioFormField,
)

_AGE_LABEL = re.compile(
    r"\b(age|aged|born|birth|dob|birthday|graduat\w*)\b",
    re.IGNORECASE,
)
_EXPERIENCE_LABEL = re.compile(r"\bexperience\b", re.IGNORECASE)


@dataclass(frozen=True)
class KnockoutFailure:
    field_id: UUID
    reason: str


@dataclass(frozen=True)
class AnswersScore:
    score: int
    breakdown: list[dict[str, Any]]


@dataclass(frozen=True)
class FormWarning:
    field_id: UUID
    message: str


def config_version(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def _is_number(value: object) -> TypeGuard[int | float]:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def evaluate_knockouts(fields: list[FormField], answers: dict[str, Any]) -> list[KnockoutFailure]:
    failures: list[KnockoutFailure] = []
    for field in fields:
        answer = answers.get(str(field.id))
        if isinstance(field, NumberFormField) and field.knockout is not None:
            failed = not _is_number(answer) or float(answer) < field.knockout.min
        elif isinstance(field, (DropdownFormField, RadioFormField)) and field.knockout is not None:
            failed = answer not in field.knockout.allowed_values
        else:
            continue
        if failed:
            failures.append(KnockoutFailure(field.id, field.knockout.reason))
    return failures


def has_knockouts(fields: list[FormField]) -> bool:
    return any(getattr(field, "knockout", None) is not None for field in fields)


def _weighted(field: FormField, answer: object) -> tuple[float, float] | None:
    """Return (weight, 0-1 fraction) for a scored field, or None when it has no scoring."""
    if isinstance(field, NumberFormField):
        if field.scoring is None:
            return None
        if not _is_number(answer):
            return field.scoring.weight, 0.0
        fraction = max(0.0, min(1.0, float(answer) / field.scoring.target))
        return field.scoring.weight, fraction
    if isinstance(field, (DropdownFormField, RadioFormField, CheckboxesFormField)):
        if field.scoring is None:
            return None
        selected = [answer] if isinstance(answer, str) else answer
        if not isinstance(selected, list):
            return field.scoring.weight, 0.0
        points = sum(field.scoring.option_scores.get(item, 0.0) for item in selected)
        return field.scoring.weight, min(1.0, points)
    return None


def score_answers(fields: list[FormField], answers: dict[str, Any]) -> AnswersScore | None:
    """Weighted 0-100 score over fields that have scoring. None if nothing is scored."""
    breakdown: list[dict[str, Any]] = []
    weighted = 0.0
    total_weight = 0.0
    for field in fields:
        scored = _weighted(field, answers.get(str(field.id)))
        if scored is None:
            continue
        weight, fraction = scored
        weighted += weight * fraction
        total_weight += weight
        breakdown.append(
            {"field_id": str(field.id), "weight": weight, "fraction": round(fraction, 4)}
        )
    if total_weight == 0:
        return None
    return AnswersScore(score=round(100 * weighted / total_weight), breakdown=breakdown)


def age_proxy_warnings(fields: list[FormField]) -> list[FormWarning]:
    """Flag knockouts that may screen by age. Warnings never block saving."""
    warnings: list[FormWarning] = []
    for field in fields:
        knockout = getattr(field, "knockout", None)
        if knockout is None:
            continue
        if _AGE_LABEL.search(field.label):
            warnings.append(
                FormWarning(
                    field.id,
                    "This knockout may act as an age filter (date of birth, age or "
                    "graduation year). Consider removing it.",
                )
            )
        elif (
            isinstance(field, (DropdownFormField, RadioFormField))
            and field.knockout is not None
            and _EXPERIENCE_LABEL.search(field.label)
            and field.options[-1] not in field.knockout.allowed_values
        ):
            warnings.append(
                FormWarning(
                    field.id,
                    "This knockout rejects the most experienced applicants. A maximum "
                    "amount of experience can act as an age filter.",
                )
            )
    return warnings
