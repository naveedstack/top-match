from typing import Any
from uuid import uuid4

import pytest

from app.schemas.forms import FormField, form_fields_adapter
from app.services.guardrail import (
    REQUIREMENTS_TARGET,
    check_form_fields,
    check_requirements,
    protected_categories_in,
)
from app.services.screening import form_warnings
from tests.support.conditions import yes_no_condition


def _question(label: str, **extra: Any) -> dict[str, Any]:
    return {"id": str(uuid4()), "type": "text", "label": label, "required": False, **extra}


def _fields(*raw: dict[str, Any]) -> list[FormField]:
    return form_fields_adapter.validate_python(list(raw))


def _keys(text: str) -> list[str]:
    return [category.key for category in protected_categories_in(text)]


@pytest.mark.parametrize(
    ("text", "category"),
    [
        ("What is your gender?", "gender"),
        ("Male candidates only", "gender"),
        ("FEMALES preferred", "gender"),
        ("What is your age?", "age"),
        ("Date of birth", "age"),
        ("Candidates must be under 30 years old", "age"),
        ("What is your marital status?", "marital_status"),
        ("Are you married?", "marital_status"),
        ("What is your religion?", "religion"),
        ("Muslim candidates preferred", "religion"),
        ("Which sect do you follow?", "religion"),
        ("What is your ethnicity?", "ethnicity"),
        ("Which caste do you belong to?", "ethnicity"),
        ("What is your race?", "ethnicity"),
        ("What is your nationality?", "nationality"),
        ("Are you a Pakistani citizen?", "nationality"),
        ("Pakistani nationals only", "nationality"),
        ("Which province is your domicile?", "nationality"),
        ("Do you have a disability?", "disability"),
        ("Any medical condition we should know of?", "disability"),
        ("Upload a recent photo", "photo"),
        ("Attach a passport size picture", "photo"),
    ],
)
def test_protected_categories_are_detected(text: str, category: str) -> None:
    assert category in _keys(text)


@pytest.mark.parametrize(
    "text",
    [
        "Are you authorized to work in Pakistan?",
        "Are you legally authorised to work in the UK?",
        "Do you have the right to work in the UAE?",
        "Can you legally work in Pakistan?",
        "Experience debugging race conditions",
        "Agile delivery and stakeholder management",
        "Average order value and page usage analytics",
        "Message queues, storage and caching",
        "Photo editing in Lightroom",
        "Photography portfolio",
        "Public sector experience",
        "Multinational client experience",
        "Expected monthly salary",
        "Are you based in Lahore or willing to relocate?",
        "Can you work USA/UK shift hours?",
        "Do you hold a valid PEC license?",
        "What is your English level?",
        "When could you start?",
        "Python, FastAPI, PostgreSQL",
    ],
)
def test_legitimate_wording_passes(text: str) -> None:
    assert _keys(text) == []


def test_form_fields_check_options_help_text_and_summary() -> None:
    options = _question("Which applies to you?") | {
        "type": "radio",
        "required": True,
        "options": ["Male", "Female"],
    }
    help_text = _question("Tell us about yourself", help_text="Include your date of birth")
    summary = yes_no_condition("travel", "info", "Can you travel?")
    summary["condition"]["summary"] = "Unmarried candidates only"

    violations = check_form_fields(_fields(options, help_text, summary))

    assert [(item.target, item.category) for item in violations] == [
        (options["id"], "gender"),
        (help_text["id"], "age"),
        (summary["id"], "marital_status"),
    ]


def test_violation_explains_and_suggests() -> None:
    field = _question("What is your nationality?")

    [violation] = check_form_fields(_fields(field))

    assert "nationality or citizenship" in violation.message
    assert violation.suggestion == "Ask about work authorization instead of nationality."
    assert set(violation.dump()) == {"target", "category", "message", "suggestion"}


def test_requirements_text_is_checked() -> None:
    violations = check_requirements("5 years of Go. Male candidates aged 25-35.")

    assert {item.category for item in violations} == {"gender", "age"}
    assert all(item.target == REQUIREMENTS_TARGET for item in violations)
    assert check_requirements("5 years of Go. Comfortable with race conditions.") == []


@pytest.mark.parametrize(
    "label",
    [
        "What is your current salary?",
        "Last drawn salary",
        "Previous CTC",
        "Please share your salary history",
    ],
)
def test_salary_history_questions_warn(label: str) -> None:
    field = _question(label)

    warnings = form_warnings(_fields(field))

    assert [str(item.field_id) for item in warnings] == [field["id"]]
    assert "expected salary" in warnings[0].message


def test_expected_salary_does_not_warn() -> None:
    assert form_warnings(_fields(_question("What is your expected salary?"))) == []
