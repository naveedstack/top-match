"""Job conditions: non-technical requirements the candidate answers on the form.

A condition is a form field tagged with `condition`. Its importance decides which Step 1
mechanism applies: must is a knockout, preferred is answer scoring, info has neither.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MAX_CONDITIONS = 10
SUMMARY_MAX = 200

type ConditionPreset = Literal[
    "work_authorization",
    "location",
    "work_mode",
    "working_hours",
    "english_level",
    "notice_period",
    "expected_salary",
    "credential",
    "travel",
]
type ConditionImportance = Literal["must", "preferred", "info"]
type ScaleDirection = Literal["at_least", "at_most"]

ENGLISH_LEVELS: tuple[str, ...] = ("Basic", "Conversational", "Professional", "Fluent")
NOTICE_PERIODS: tuple[str, ...] = (
    "Immediately",
    "Within 2 weeks",
    "Within 1 month",
    "Within 2 months",
    "More than 2 months",
)

# Presets whose options are a fixed, ordered scale, and which end of the scale passes.
ORDERED_SCALES: dict[ConditionPreset, tuple[tuple[str, ...], ScaleDirection]] = {
    "english_level": (ENGLISH_LEVELS, "at_least"),
    "notice_period": (NOTICE_PERIODS, "at_most"),
}

PRESET_FIELD_TYPE: dict[ConditionPreset, Literal["number", "dropdown", "radio"]] = {
    "work_authorization": "radio",
    "location": "radio",
    "work_mode": "radio",
    "working_hours": "radio",
    "english_level": "dropdown",
    "notice_period": "dropdown",
    "expected_salary": "number",
    "credential": "radio",
    "travel": "radio",
}


class SalaryRange(BaseModel):
    """The job's salary range. Expected salaries at or below max pass."""

    model_config = ConfigDict(extra="forbid")

    currency: str = Field(pattern=r"^[A-Z]{3}$")
    min: float = Field(ge=0)
    max: float = Field(gt=0)

    @model_validator(mode="after")
    def min_lte_max(self) -> SalaryRange:
        if self.min > self.max:
            raise ValueError("salary min must be less than or equal to max")
        return self


class JobCondition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preset: ConditionPreset
    importance: ConditionImportance
    # Candidate-facing line shown under "Before you apply" for must conditions.
    summary: str = Field(min_length=1, max_length=SUMMARY_MAX)
    salary: SalaryRange | None = None

    @field_validator("summary")
    @classmethod
    def strip_summary(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @model_validator(mode="after")
    def salary_only_for_salary(self) -> JobCondition:
        if (self.preset == "expected_salary") != (self.salary is not None):
            raise ValueError("salary range is required for expected salary, and only for it")
        return self


def is_contiguous_from(
    values: list[str], scale: tuple[str, ...], direction: ScaleDirection
) -> bool:
    """True when `values` is the run of the scale from some level up (or down) to its end."""
    if not values or not set(values) <= set(scale):
        return False
    count = len(set(values))
    expected = scale[-count:] if direction == "at_least" else scale[:count]
    return set(values) == set(expected)


# Recruiter-facing outcome: must is pass/fail, preferred can be partial, info is not scored.
type ConditionVerdict = Literal["pass", "partial", "fail", "not_scored"]
