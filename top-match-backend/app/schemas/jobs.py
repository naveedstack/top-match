from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import ApplicationStatus, JobStatus
from app.schemas.forms import FormField, validate_form_fields


def _require_stripped(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("must not be blank")
    return stripped


class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    requirements: str = Field(min_length=1)
    form_fields: list[FormField] = Field(default_factory=list)

    @field_validator("title", "description", "requirements")
    @classmethod
    def strip_not_blank(cls, value: str) -> str:
        return _require_stripped(value)

    @field_validator("form_fields")
    @classmethod
    def check_form_fields(cls, value: list[FormField]) -> list[FormField]:
        return validate_form_fields(value)


class JobUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1)
    requirements: str | None = Field(default=None, min_length=1)
    form_fields: list[FormField] | None = None

    @field_validator("title", "description", "requirements")
    @classmethod
    def strip_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _require_stripped(value)

    @field_validator("form_fields")
    @classmethod
    def check_form_fields(cls, value: list[FormField] | None) -> list[FormField] | None:
        if value is None:
            return None
        return validate_form_fields(value)


class ApplicationCounts(BaseModel):
    received: int
    processing: int
    scored: int
    refused: int
    failed: int

    @classmethod
    def from_status_map(cls, counts: dict[ApplicationStatus, int]) -> ApplicationCounts:
        return cls(
            received=counts[ApplicationStatus.RECEIVED],
            processing=counts[ApplicationStatus.PROCESSING],
            scored=counts[ApplicationStatus.SCORED],
            refused=counts[ApplicationStatus.REFUSED],
            failed=counts[ApplicationStatus.FAILED],
        )


class JobResponse(BaseModel):
    id: UUID
    title: str
    description: str
    requirements: str
    form_fields: list[FormField]
    company_slug: str
    public_slug: str
    public_url: str
    status: JobStatus
    created_at: datetime
    closed_at: datetime | None


class JobListItemResponse(JobResponse):
    application_counts: ApplicationCounts


class JobDetailResponse(JobResponse):
    application_counts: ApplicationCounts
    screening_disclaimer: str
    form_locked: bool


class PublicJobResponse(BaseModel):
    title: str
    description: str
    requirements: str
    form_fields: list[FormField]
    company_slug: str
    status: JobStatus
    privacy_notice: str
    ai_screening_notice: str
    screening_disclaimer: str
