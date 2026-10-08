from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.forms import FormField, form_fields_adapter
from app.services.screening import (
    config_version,
    evaluate_knockouts,
    form_warnings,
    score_answers,
)


def _fields(*raw: dict[str, Any]) -> list[FormField]:
    return form_fields_adapter.validate_python(list(raw))


def _yes_no(label: str = "Are you authorized to work in Pakistan?") -> dict[str, Any]:
    return {
        "id": str(uuid4()),
        "type": "radio",
        "label": label,
        "required": True,
        "options": ["Yes", "No"],
        "knockout": {"reason": "Not authorized to work in Pakistan", "allowed_values": ["Yes"]},
    }


def _years(**overrides: Any) -> dict[str, Any]:
    field: dict[str, Any] = {
        "id": str(uuid4()),
        "type": "number",
        "label": "Years of Python",
        "required": True,
        "knockout": {"reason": "Fewer than 3 years of Python", "min": 3},
    }
    field.update(overrides)
    return field


def _dropdown(**overrides: Any) -> dict[str, Any]:
    field: dict[str, Any] = {
        "id": str(uuid4()),
        "type": "dropdown",
        "label": "Notice period",
        "required": True,
        "options": ["Immediate", "1 month", "3 months"],
        "knockout": {
            "reason": "Notice period too long",
            "allowed_values": ["Immediate", "1 month"],
        },
    }
    field.update(overrides)
    return field


def test_yes_no_knockout_passes_and_fails() -> None:
    raw = _yes_no()
    fields = _fields(raw)

    assert evaluate_knockouts(fields, {raw["id"]: "Yes"}) == []
    failures = evaluate_knockouts(fields, {raw["id"]: "No"})
    assert [item.reason for item in failures] == ["Not authorized to work in Pakistan"]


def test_number_knockout_uses_minimum() -> None:
    raw = _years()
    fields = _fields(raw)

    assert evaluate_knockouts(fields, {raw["id"]: 3}) == []
    assert evaluate_knockouts(fields, {raw["id"]: 7.5}) == []
    assert len(evaluate_knockouts(fields, {raw["id"]: 2})) == 1


def test_dropdown_knockout_uses_allowed_values() -> None:
    raw = _dropdown()
    fields = _fields(raw)

    assert evaluate_knockouts(fields, {raw["id"]: "1 month"}) == []
    assert len(evaluate_knockouts(fields, {raw["id"]: "3 months"})) == 1


def test_missing_knockout_answer_fails() -> None:
    raw = _yes_no()

    assert len(evaluate_knockouts(_fields(raw), {})) == 1


def test_every_failed_knockout_is_reported() -> None:
    first, second = _yes_no(), _years()

    failures = evaluate_knockouts(_fields(first, second), {first["id"]: "No", second["id"]: 1})

    assert {str(item.field_id) for item in failures} == {first["id"], second["id"]}


def test_knockout_must_be_required() -> None:
    with pytest.raises(ValidationError, match="knockout questions must be required"):
        _fields(_yes_no() | {"required": False})
    with pytest.raises(ValidationError, match="knockout questions must be required"):
        _fields(_years(required=False))


def test_knockout_allowed_values_must_be_options() -> None:
    raw = _dropdown(knockout={"reason": "x", "allowed_values": ["Tomorrow"]})

    with pytest.raises(ValidationError, match="allowed values must be field options"):
        _fields(raw)


def test_checkboxes_cannot_be_knockouts() -> None:
    raw = {
        "id": str(uuid4()),
        "type": "checkboxes",
        "label": "Skills",
        "required": True,
        "options": ["Python", "Go"],
        "knockout": {"reason": "x", "allowed_values": ["Python"]},
    }

    with pytest.raises(ValidationError):
        _fields(raw)


def test_answers_score_weights_fields() -> None:
    choice = {
        "id": str(uuid4()),
        "type": "radio",
        "label": "Remote?",
        "required": True,
        "options": ["Yes", "No"],
        "scoring": {"weight": 1, "option_scores": {"Yes": 1, "No": 0}},
    }
    years = {
        "id": str(uuid4()),
        "type": "number",
        "label": "Years of Go",
        "required": True,
        "scoring": {"weight": 3, "target": 4},
    }
    skills = {
        "id": str(uuid4()),
        "type": "checkboxes",
        "label": "Skills",
        "required": True,
        "options": ["Python", "Go", "Rust"],
        "scoring": {"weight": 2, "option_scores": {"Python": 0.5, "Go": 0.75}},
    }
    fields = _fields(choice, years, skills)

    result = score_answers(fields, {choice["id"]: "Yes", years["id"]: 2, skills["id"]: ["Python"]})

    assert result is not None
    # (1*1 + 3*0.5 + 2*0.5) / 6 = 0.5833
    assert result.score == 58
    assert len(result.breakdown) == 3

    full = score_answers(
        fields, {choice["id"]: "Yes", years["id"]: 10, skills["id"]: ["Python", "Go"]}
    )
    assert full is not None and full.score == 100


def test_answers_score_is_none_without_scoring() -> None:
    assert score_answers(_fields(_yes_no()), {}) is None


def test_scored_options_must_exist() -> None:
    raw = _dropdown(knockout=None, scoring={"weight": 1, "option_scores": {"Never": 1}})

    with pytest.raises(ValidationError, match="scored options must be field options"):
        _fields(raw)


@pytest.mark.parametrize("label", ["Year of graduation", "When did you graduate?"])
def test_graduation_year_knockout_warns(label: str) -> None:
    raw = _dropdown(label=label)

    warnings = form_warnings(_fields(raw))

    assert [str(item.field_id) for item in warnings] == [raw["id"]]


def test_experience_cap_warns() -> None:
    raw = _dropdown(
        label="Years of experience",
        options=["0-2", "3-5", "6-10", "10+"],
        knockout={"reason": "Too senior", "allowed_values": ["3-5", "6-10"]},
    )

    assert len(form_warnings(_fields(raw))) == 1


def test_ordinary_knockouts_do_not_warn() -> None:
    experience_floor = _dropdown(
        label="Years of experience",
        options=["0-2", "3-5", "6-10", "10+"],
        knockout={"reason": "Too junior", "allowed_values": ["3-5", "6-10", "10+"]},
    )
    plain_age_question = {
        "id": str(uuid4()),
        "type": "text",
        "label": "Graduation year",
        "required": False,
    }

    assert form_warnings(_fields(_yes_no(), _years(), experience_floor)) == []
    assert form_warnings(_fields(plain_age_question)) == []


def test_config_version_is_stable() -> None:
    assert config_version({"b": 1, "a": [2]}) == config_version({"a": [2], "b": 1})
    assert config_version({"a": 1}) != config_version({"a": 2})
