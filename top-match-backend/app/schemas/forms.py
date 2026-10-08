from __future__ import annotations

from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, field_validator, model_validator

from app.schemas.conditions import (
    MAX_CONDITIONS,
    ORDERED_SCALES,
    PRESET_FIELD_TYPE,
    JobCondition,
    ScaleDirection,
    is_contiguous_from,
)

MAX_FORM_FIELDS = 20
MAX_FILE_FIELDS = 5
LABEL_MAX = 200
HELP_MAX = 500
OPTION_MAX = 200
MIN_OPTIONS = 2
MAX_OPTIONS = 50
TEXT_MAX_LENGTH_DEFAULT = 500
TEXT_MAX_LENGTH_CAP = 5000
KNOCKOUT_REASON_MAX = 300
MAX_WEIGHT = 10

type FileAccept = Literal["pdf", "docx", "png", "jpeg"]

ACCEPT_MIME: dict[FileAccept, str] = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "png": "image/png",
    "jpeg": "image/jpeg",
}
MIME_TO_ACCEPT: dict[str, FileAccept] = {mime: key for key, mime in ACCEPT_MIME.items()}


class FormFieldBase(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    label: str = Field(min_length=1, max_length=LABEL_MAX)
    help_text: str | None = Field(default=None, max_length=HELP_MAX)
    required: bool = False

    @field_validator("label")
    @classmethod
    def strip_label(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped

    @field_validator("help_text")
    @classmethod
    def strip_help(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


class ConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class KnockoutBase(ConfigModel):
    # Shown to the recruiter when an applicant fails this knockout.
    reason: str = Field(min_length=1, max_length=KNOCKOUT_REASON_MAX)

    @field_validator("reason")
    @classmethod
    def strip_reason(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be blank")
        return stripped


class ChoiceKnockout(KnockoutBase):
    """Fails unless the answer is one of allowed_values. Yes/no is a radio preset."""

    allowed_values: list[str] = Field(min_length=1)


class NumberKnockout(KnockoutBase):
    """Fails when the answer is below min or above max."""

    min: float | None = None
    max: float | None = None

    @model_validator(mode="after")
    def check_bounds(self) -> NumberKnockout:
        if self.min is None and self.max is None:
            raise ValueError("a number knockout needs a min or a max")
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("knockout min must be less than or equal to max")
        return self


class ChoiceScoring(ConfigModel):
    """Points per option (0-1), scaled by weight. Unlisted options score 0."""

    weight: float = Field(gt=0, le=MAX_WEIGHT)
    option_scores: dict[str, float]

    @field_validator("option_scores")
    @classmethod
    def scores_in_range(cls, value: dict[str, float]) -> dict[str, float]:
        if any(score < 0 or score > 1 for score in value.values()):
            raise ValueError("option scores must be between 0 and 1")
        return value


class NumberScoring(ConfigModel):
    """Full points on the target's side ("at_least" or "at_most"), scaled linearly beyond it."""

    weight: float = Field(gt=0, le=MAX_WEIGHT)
    target: float = Field(gt=0)
    direction: ScaleDirection = "at_least"


def _check_condition(
    condition: JobCondition | None,
    field_type: str,
    *,
    has_knockout: bool,
    has_scoring: bool,
) -> None:
    """Importance decides the mechanism: must = knockout, preferred = scoring, info = neither."""
    if condition is None:
        return
    if PRESET_FIELD_TYPE[condition.preset] != field_type:
        raise ValueError(
            f"{condition.preset} conditions must be {PRESET_FIELD_TYPE[condition.preset]} fields"
        )
    expected = {"must": (True, False), "preferred": (False, True), "info": (False, False)}
    if (has_knockout, has_scoring) != expected[condition.importance]:
        raise ValueError(
            "must conditions need a knockout, preferred conditions need scoring, "
            "and info conditions need neither"
        )


class TextFormField(FormFieldBase):
    type: Literal["text"] = "text"
    multiline: bool = False
    max_length: int = Field(default=TEXT_MAX_LENGTH_DEFAULT, ge=1, le=TEXT_MAX_LENGTH_CAP)


class NumberFormField(FormFieldBase):
    type: Literal["number"] = "number"
    min: float | None = None
    max: float | None = None
    integer_only: bool = False
    knockout: NumberKnockout | None = None
    scoring: NumberScoring | None = None
    condition: JobCondition | None = None

    @model_validator(mode="after")
    def min_lte_max(self) -> NumberFormField:
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("min must be less than or equal to max")
        if self.knockout is not None and not self.required:
            raise ValueError("knockout questions must be required")
        _check_condition(
            self.condition,
            self.type,
            has_knockout=self.knockout is not None,
            has_scoring=self.scoring is not None,
        )
        self._check_salary_matches_range()
        return self

    def _check_salary_matches_range(self) -> None:
        """Salary knockout and scoring must use the condition's range maximum."""
        salary = None if self.condition is None else self.condition.salary
        if salary is None:
            return
        if self.knockout is not None and (
            self.knockout.min is not None or self.knockout.max != salary.max
        ):
            raise ValueError("a salary knockout must use the range maximum as its only limit")
        if self.scoring is not None and (
            self.scoring.direction != "at_most" or self.scoring.target != salary.max
        ):
            raise ValueError("salary scoring must target the range maximum, at most")


class ChoiceFormField(FormFieldBase):
    options: list[str] = Field(min_length=MIN_OPTIONS, max_length=MAX_OPTIONS)

    @field_validator("options")
    @classmethod
    def unique_stripped_options(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for item in value:
            stripped = item.strip()
            if not stripped:
                raise ValueError("options must not be blank")
            if len(stripped) > OPTION_MAX:
                raise ValueError(f"options must be at most {OPTION_MAX} characters")
            if stripped in seen:
                raise ValueError("options must be unique")
            seen.add(stripped)
            cleaned.append(stripped)
        return cleaned

    def _check_option_scores(self, scoring: ChoiceScoring | None) -> None:
        if scoring is not None and not set(scoring.option_scores) <= set(self.options):
            raise ValueError("scored options must be field options")


class KnockoutChoiceFormField(ChoiceFormField):
    type: Literal["dropdown", "radio"]
    knockout: ChoiceKnockout | None = None
    scoring: ChoiceScoring | None = None
    condition: JobCondition | None = None

    @model_validator(mode="after")
    def check_knockout_and_scoring(self) -> KnockoutChoiceFormField:
        if self.knockout is not None:
            if not self.required:
                raise ValueError("knockout questions must be required")
            if not set(self.knockout.allowed_values) <= set(self.options):
                raise ValueError("allowed values must be field options")
        self._check_option_scores(self.scoring)
        _check_condition(
            self.condition,
            self.type,
            has_knockout=self.knockout is not None,
            has_scoring=self.scoring is not None,
        )
        self._check_ordered_scale()
        return self

    def _check_ordered_scale(self) -> None:
        """Scale presets keep their fixed options; a knockout passes one end of the scale."""
        if self.condition is None or self.condition.preset not in ORDERED_SCALES:
            return
        scale, direction = ORDERED_SCALES[self.condition.preset]
        if tuple(self.options) != scale:
            raise ValueError(f"options must be {', '.join(scale)} in that order")
        if self.knockout is not None and not is_contiguous_from(
            self.knockout.allowed_values, scale, direction
        ):
            limit = "minimum" if direction == "at_least" else "maximum"
            raise ValueError(
                f"allowed values must run from a {limit} level to the end of the scale"
            )


class DropdownFormField(KnockoutChoiceFormField):
    type: Literal["dropdown"] = "dropdown"


class RadioFormField(KnockoutChoiceFormField):
    type: Literal["radio"] = "radio"


class CheckboxesFormField(ChoiceFormField):
    type: Literal["checkboxes"] = "checkboxes"
    scoring: ChoiceScoring | None = None

    @model_validator(mode="after")
    def check_scoring(self) -> CheckboxesFormField:
        self._check_option_scores(self.scoring)
        return self


class FileFormField(FormFieldBase):
    type: Literal["file"] = "file"
    accept: list[FileAccept] = Field(min_length=1)

    @field_validator("accept")
    @classmethod
    def unique_accept(cls, value: list[FileAccept]) -> list[FileAccept]:
        if len(set(value)) != len(value):
            raise ValueError("accept must be unique")
        return value


type FormField = Annotated[
    TextFormField
    | NumberFormField
    | DropdownFormField
    | RadioFormField
    | CheckboxesFormField
    | FileFormField,
    Field(discriminator="type"),
]

form_fields_adapter: TypeAdapter[list[FormField]] = TypeAdapter(list[FormField])


def condition_of(field: FormField) -> JobCondition | None:
    return (
        field.condition if isinstance(field, (NumberFormField, KnockoutChoiceFormField)) else None
    )


def validate_form_fields(fields: list[FormField]) -> list[FormField]:
    conditions = sum(1 for field in fields if condition_of(field) is not None)
    if len(fields) - conditions > MAX_FORM_FIELDS:
        raise ValueError(f"A form can have at most {MAX_FORM_FIELDS} custom questions")
    if conditions > MAX_CONDITIONS:
        raise ValueError(f"A form can have at most {MAX_CONDITIONS} job conditions")
    ids = [field.id for field in fields]
    if len(ids) != len(set(ids)):
        raise ValueError("Field ids must be unique")
    file_count = sum(1 for field in fields if field.type == "file")
    if file_count > MAX_FILE_FIELDS:
        raise ValueError(f"A form can have at most {MAX_FILE_FIELDS} file fields")
    return fields


def dump_form_fields(fields: list[FormField]) -> list[dict[str, Any]]:
    return [field.model_dump(mode="json") for field in fields]


def parse_form_fields(raw: object) -> list[FormField]:
    if not raw:
        return []
    return form_fields_adapter.validate_python(raw)
