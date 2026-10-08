"""Job condition outcomes. Evaluation reuses the Step 1 knockout and answer-scoring checks."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from app.models import ReasonCode
from app.schemas.conditions import ConditionVerdict, JobCondition
from app.schemas.forms import FormField, condition_of
from app.services.screening import knockout_passed, weighted_answer


@dataclass(frozen=True)
class ConditionOutcome:
    condition: JobCondition
    verdict: ConditionVerdict


def _preferred_verdict(field: FormField, answer: object) -> ConditionVerdict:
    scored = weighted_answer(field, answer)
    fraction = 0.0 if scored is None else scored[1]
    if fraction >= 1:
        return "pass"
    return "fail" if fraction <= 0 else "partial"


def evaluate_condition(field: FormField, answer: object) -> ConditionOutcome | None:
    """The outcome of one condition answer, or None when the field is not a condition."""
    condition = condition_of(field)
    if condition is None:
        return None
    verdict: ConditionVerdict
    if condition.importance == "must":
        verdict = "pass" if knockout_passed(field, answer) else "fail"
    elif condition.importance == "preferred":
        verdict = _preferred_verdict(field, answer)
    else:
        verdict = "not_scored"
    return ConditionOutcome(condition, verdict)


def must_conditions(fields: list[FormField]) -> list[tuple[FormField, JobCondition]]:
    pairs = [(field, condition_of(field)) for field in fields]
    return [
        (field, condition)
        for field, condition in pairs
        if condition is not None and condition.importance == "must"
    ]


def before_you_apply(fields: list[FormField]) -> list[str]:
    """Candidate-facing summaries of the must conditions, in form order."""
    return [condition.summary for _field, condition in must_conditions(fields)]


def failed_condition_labels(fields: list[FormField], reasons: list[dict[str, Any]]) -> list[str]:
    """Labels of the conditions named in knockout failure reasons."""
    failed = {
        UUID(reason["field_id"])
        for reason in reasons
        if reason.get("code") == ReasonCode.KNOCKOUT_FAILED.value and "field_id" in reason
    }
    return [
        field.label for field in fields if field.id in failed and condition_of(field) is not None
    ]
