from typing import Any
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.conditions import ENGLISH_LEVELS, NOTICE_PERIODS, is_contiguous_from
from app.schemas.forms import FormField, form_fields_adapter, validate_form_fields
from app.services.conditions import (
    before_you_apply,
    evaluate_condition,
    failed_condition_labels,
)
from app.services.screening import evaluate_knockouts, score_answers
from tests.support.conditions import (
    SALARY,
    all_presets,
    english_condition,
    notice_condition,
    salary_condition,
    yes_no_condition,
)


def _fields(*raw: dict[str, Any]) -> list[FormField]:
    return form_fields_adapter.validate_python(list(raw))


def _one(raw: dict[str, Any]) -> FormField:
    return _fields(raw)[0]


def _verdict(field: FormField, answer: object) -> str:
    outcome = evaluate_condition(field, answer)
    assert outcome is not None
    return outcome.verdict


def _preset_id(case: tuple[dict[str, Any], object, object]) -> str:
    return str(case[0]["condition"]["preset"])


@pytest.mark.parametrize("case", all_presets("must"), ids=_preset_id)
def test_must_condition_is_a_knockout(case: tuple[dict[str, Any], object, object]) -> None:
    raw, passing, failing = case
    fields = _fields(raw)

    assert evaluate_knockouts(fields, {raw["id"]: passing}) == []
    failures = evaluate_knockouts(fields, {raw["id"]: failing})
    assert [str(item.field_id) for item in failures] == [raw["id"]]
    assert score_answers(fields, {raw["id"]: passing}) is None
    assert _verdict(fields[0], passing) == "pass"
    assert _verdict(fields[0], failing) == "fail"


@pytest.mark.parametrize("case", all_presets("preferred"), ids=_preset_id)
def test_preferred_condition_adds_to_answers_score(
    case: tuple[dict[str, Any], object, object],
) -> None:
    raw, passing, failing = case
    fields = _fields(raw)

    assert evaluate_knockouts(fields, {raw["id"]: failing}) == []
    best = score_answers(fields, {raw["id"]: passing})
    worse = score_answers(fields, {raw["id"]: failing})
    assert best is not None and worse is not None
    assert best.score == 100
    assert worse.score < best.score
    assert _verdict(fields[0], failing) in {"fail", "partial"}


@pytest.mark.parametrize("case", all_presets("info"), ids=_preset_id)
def test_info_condition_has_no_effect(case: tuple[dict[str, Any], object, object]) -> None:
    raw, _passing, failing = case
    fields = _fields(raw)

    assert evaluate_knockouts(fields, {raw["id"]: failing}) == []
    assert score_answers(fields, {raw["id"]: failing}) is None
    assert _verdict(fields[0], failing) == "not_scored"


def test_plain_questions_have_no_condition_outcome() -> None:
    raw = {"id": str(uuid4()), "type": "text", "label": "Portfolio link", "required": False}

    assert evaluate_condition(_one(raw), "https://example.com") is None


@pytest.mark.parametrize(
    ("answer", "passes"),
    [("Basic", False), ("Conversational", False), ("Professional", True), ("Fluent", True)],
)
def test_english_level_minimum_follows_scale_order(answer: str, passes: bool) -> None:
    raw = english_condition("must", minimum="Professional")

    assert (evaluate_knockouts(_fields(raw), {raw["id"]: answer}) == []) is passes


def test_ordered_scales_accept_only_contiguous_runs() -> None:
    assert is_contiguous_from(["Professional", "Fluent"], ENGLISH_LEVELS, "at_least")
    assert not is_contiguous_from(["Basic", "Fluent"], ENGLISH_LEVELS, "at_least")
    assert not is_contiguous_from(["Basic", "Conversational"], ENGLISH_LEVELS, "at_least")
    assert is_contiguous_from(["Immediately", "Within 2 weeks"], NOTICE_PERIODS, "at_most")
    assert not is_contiguous_from(["More than 2 months"], NOTICE_PERIODS, "at_most")
    assert not is_contiguous_from([], NOTICE_PERIODS, "at_most")


def test_english_level_rejects_gaps_and_reordered_options() -> None:
    gap = english_condition("must")
    gap["knockout"]["allowed_values"] = ["Basic", "Fluent"]
    reordered = english_condition("info")
    reordered["options"] = list(reversed(ENGLISH_LEVELS))

    with pytest.raises(ValidationError, match="from a minimum level"):
        _fields(gap)
    with pytest.raises(ValidationError, match="in that order"):
        _fields(reordered)


def test_notice_period_maximum_passes_shorter_notice() -> None:
    raw = notice_condition("must", maximum="Within 1 month")
    fields = _fields(raw)

    assert evaluate_knockouts(fields, {raw["id"]: "Immediately"}) == []
    assert len(evaluate_knockouts(fields, {raw["id"]: "Within 2 months"})) == 1


@pytest.mark.parametrize(
    ("expected", "passes"),
    [(100_000, True), (150_000, True), (250_000, True), (250_001, False), (400_000, False)],
)
def test_salary_must_passes_at_or_below_range_max(expected: int, passes: bool) -> None:
    raw = salary_condition("must")

    assert (evaluate_knockouts(_fields(raw), {raw["id"]: expected}) == []) is passes


def test_salary_preferred_scales_down_above_range() -> None:
    raw = salary_condition("preferred")
    fields = _fields(raw)

    below = score_answers(fields, {raw["id"]: 90_000})
    above = score_answers(fields, {raw["id"]: 500_000})
    assert below is not None and below.score == 100
    assert above is not None and above.score == 50
    assert _verdict(fields[0], 500_000) == "partial"


@pytest.mark.parametrize(
    "change",
    [
        {"knockout": {"reason": "Too high", "max": 999_999}},
        {"knockout": {"reason": "Too low", "min": 150_000, "max": SALARY["max"]}},
    ],
)
def test_salary_knockout_must_match_range(change: dict[str, Any]) -> None:
    with pytest.raises(ValidationError, match="range maximum"):
        _fields(salary_condition("must") | change)


def test_salary_scoring_must_target_range_max_at_most() -> None:
    raw = salary_condition("preferred") | {"scoring": {"weight": 1, "target": SALARY["max"]}}

    with pytest.raises(ValidationError, match="range maximum"):
        _fields(raw)


def test_salary_range_is_required_and_valid() -> None:
    missing = salary_condition("info")
    del missing["condition"]["salary"]
    bad_currency = salary_condition("info")
    bad_currency["condition"]["salary"] = SALARY | {"currency": "rupees"}
    inverted = salary_condition("info")
    inverted["condition"]["salary"] = SALARY | {"min": 300_000}

    for raw in (missing, bad_currency, inverted):
        with pytest.raises(ValidationError):
            _fields(raw)


def test_salary_range_is_only_for_salary() -> None:
    raw = yes_no_condition("travel", "info", "Can you travel?")
    raw["condition"]["salary"] = SALARY

    with pytest.raises(ValidationError, match="salary range is required"):
        _fields(raw)


@pytest.mark.parametrize(
    ("importance", "drop", "add"),
    [
        ("must", "knockout", None),
        ("preferred", "scoring", None),
        ("info", None, {"knockout": {"reason": "x", "allowed_values": ["Yes"]}}),
    ],
)
def test_importance_must_match_knockout_and_scoring(
    importance: str, drop: str | None, add: dict[str, Any] | None
) -> None:
    raw = yes_no_condition("travel", importance, "Can you travel?")
    if drop is not None:
        raw[drop] = None
    raw.update(add or {})

    with pytest.raises(ValidationError, match="must conditions need a knockout"):
        _fields(raw)


def test_preset_requires_its_field_type() -> None:
    raw = yes_no_condition("travel", "info", "Can you travel?") | {"type": "dropdown"}
    raw["condition"]["preset"] = "expected_salary"
    raw["condition"]["salary"] = SALARY

    with pytest.raises(ValidationError, match="must be number fields"):
        _fields(raw)


def _questions(count: int) -> list[dict[str, Any]]:
    return [
        {"id": str(uuid4()), "type": "text", "label": f"Question {index}", "required": False}
        for index in range(count)
    ]


def _conditions(count: int) -> list[dict[str, Any]]:
    return [yes_no_condition("travel", "info", f"Condition {index}") for index in range(count)]


def test_questions_and_conditions_have_separate_limits() -> None:
    assert len(validate_form_fields(_fields(*_questions(20), *_conditions(10)))) == 30
    with pytest.raises(ValueError, match="at most 20 custom questions"):
        validate_form_fields(_fields(*_questions(21)))
    with pytest.raises(ValueError, match="at most 10 job conditions"):
        validate_form_fields(_fields(*_conditions(11)))


def test_before_you_apply_lists_must_summaries_in_order() -> None:
    first = yes_no_condition("work_authorization", "must", "Can you legally work in Pakistan?")
    preferred = yes_no_condition("travel", "preferred", "Can you travel?")
    second = english_condition("must")

    assert before_you_apply(_fields(first, preferred, second)) == [
        "Can you legally work in Pakistan? summary",
        "English level summary",
    ]


def test_failed_condition_labels_ignore_plain_knockouts() -> None:
    condition = yes_no_condition("work_authorization", "must", "Can you legally work here?")
    plain = {
        "id": str(uuid4()),
        "type": "radio",
        "label": "Do you own a laptop?",
        "required": True,
        "options": ["Yes", "No"],
        "knockout": {"reason": "No laptop", "allowed_values": ["Yes"]},
    }
    reasons = [
        {"code": "knockout_failed", "message": "x", "field_id": condition["id"]},
        {"code": "knockout_failed", "message": "y", "field_id": plain["id"]},
    ]

    labels = failed_condition_labels(_fields(condition, plain), reasons)

    assert labels == ["Can you legally work here?"]
