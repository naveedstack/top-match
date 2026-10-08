"""Builders for job-condition form fields, as the condition builder would send them."""

from typing import Any
from uuid import uuid4

from app.schemas.conditions import ENGLISH_LEVELS, NOTICE_PERIODS

YES_NO = ["Yes", "No"]
SALARY = {"currency": "PKR", "min": 150_000, "max": 250_000}


def _field(
    field_type: str,
    label: str,
    preset: str,
    importance: str,
    *,
    options: list[str] | None = None,
    knockout: dict[str, Any] | None = None,
    scoring: dict[str, Any] | None = None,
    salary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    condition: dict[str, Any] = {
        "preset": preset,
        "importance": importance,
        "summary": f"{label} summary",
    }
    if salary is not None:
        condition["salary"] = salary
    field: dict[str, Any] = {
        "id": str(uuid4()),
        "type": field_type,
        "label": label,
        "required": True,
        "condition": condition,
    }
    if options is not None:
        field["options"] = options
    if importance == "must":
        field["knockout"] = knockout
    elif importance == "preferred":
        field["scoring"] = scoring
    return field


def choice_condition(
    preset: str,
    importance: str,
    *,
    label: str,
    options: list[str],
    passing: list[str],
    field_type: str = "radio",
) -> dict[str, Any]:
    """A radio or dropdown condition where `passing` options pass or score full points."""
    return _field(
        field_type,
        label,
        preset,
        importance,
        options=options,
        knockout={"reason": f"Failed: {label}", "allowed_values": passing},
        scoring={"weight": 1, "option_scores": dict.fromkeys(passing, 1.0)},
    )


def yes_no_condition(preset: str, importance: str, label: str) -> dict[str, Any]:
    return choice_condition(preset, importance, label=label, options=YES_NO, passing=["Yes"])


def english_condition(importance: str, minimum: str = "Professional") -> dict[str, Any]:
    passing = list(ENGLISH_LEVELS[ENGLISH_LEVELS.index(minimum) :])
    return choice_condition(
        "english_level",
        importance,
        label="English level",
        options=list(ENGLISH_LEVELS),
        passing=passing,
        field_type="dropdown",
    )


def notice_condition(importance: str, maximum: str = "Within 1 month") -> dict[str, Any]:
    passing = list(NOTICE_PERIODS[: NOTICE_PERIODS.index(maximum) + 1])
    return choice_condition(
        "notice_period",
        importance,
        label="When could you start?",
        options=list(NOTICE_PERIODS),
        passing=passing,
        field_type="dropdown",
    )


def salary_condition(importance: str) -> dict[str, Any]:
    return _field(
        "number",
        "Expected monthly salary",
        "expected_salary",
        importance,
        knockout={"reason": "Expected salary above range", "max": SALARY["max"]},
        scoring={"weight": 1, "target": SALARY["max"], "direction": "at_most"},
        salary=SALARY,
    )


def all_presets(importance: str) -> list[tuple[dict[str, Any], object, object]]:
    """(field, passing answer, failing answer) for every preset."""
    return [
        (
            yes_no_condition("work_authorization", importance, "Can you legally work in Pakistan?"),
            "Yes",
            "No",
        ),
        (
            choice_condition(
                "location",
                importance,
                label="Are you based in Lahore or willing to relocate?",
                options=["Based in Lahore", "Willing to relocate", "Neither"],
                passing=["Based in Lahore", "Willing to relocate"],
            ),
            "Willing to relocate",
            "Neither",
        ),
        (
            choice_condition(
                "work_mode",
                importance,
                label="Which work arrangement can you commit to?",
                options=["Onsite", "Hybrid", "Remote"],
                passing=["Onsite", "Hybrid"],
            ),
            "Hybrid",
            "Remote",
        ),
        (
            yes_no_condition("working_hours", importance, "Can you work USA/UK shift hours?"),
            "Yes",
            "No",
        ),
        (english_condition(importance), "Fluent", "Conversational"),
        (notice_condition(importance), "Within 2 weeks", "More than 2 months"),
        (salary_condition(importance), 200_000, 2_500_000),
        (
            yes_no_condition("credential", importance, "Do you hold a valid PEC license?"),
            "Yes",
            "No",
        ),
        (
            yes_no_condition("travel", importance, "Can you travel up to 30% of the time?"),
            "Yes",
            "No",
        ),
    ]
