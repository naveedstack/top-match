from __future__ import annotations

from typing import Annotated, Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, field_validator, model_validator

MAX_FORM_FIELDS = 20
MAX_FILE_FIELDS = 5
LABEL_MAX = 200
HELP_MAX = 500
OPTION_MAX = 200
MIN_OPTIONS = 2
MAX_OPTIONS = 50
TEXT_MAX_LENGTH_DEFAULT = 500
TEXT_MAX_LENGTH_CAP = 5000

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


class TextFormField(FormFieldBase):
    type: Literal["text"] = "text"
    multiline: bool = False
    max_length: int = Field(default=TEXT_MAX_LENGTH_DEFAULT, ge=1, le=TEXT_MAX_LENGTH_CAP)


class NumberFormField(FormFieldBase):
    type: Literal["number"] = "number"
    min: float | None = None
    max: float | None = None
    integer_only: bool = False

    @model_validator(mode="after")
    def min_lte_max(self) -> NumberFormField:
        if self.min is not None and self.max is not None and self.min > self.max:
            raise ValueError("min must be less than or equal to max")
        return self


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


class DropdownFormField(ChoiceFormField):
    type: Literal["dropdown"] = "dropdown"


class RadioFormField(ChoiceFormField):
    type: Literal["radio"] = "radio"


class CheckboxesFormField(ChoiceFormField):
    type: Literal["checkboxes"] = "checkboxes"


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


def validate_form_fields(fields: list[FormField]) -> list[FormField]:
    if len(fields) > MAX_FORM_FIELDS:
        raise ValueError(f"A form can have at most {MAX_FORM_FIELDS} custom fields")
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
