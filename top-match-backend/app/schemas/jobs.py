from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import ApplicationStatus, JobStatus


def _require_stripped(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("must not be blank")
    return stripped


class JobCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    requirements: str = Field(min_length=1)

    @field_validator("title", "description", "requirements")
    @classmethod
    def strip_not_blank(cls, value: str) -> str:
        return _require_stripped(value)


class JobUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1)
    requirements: str | None = Field(default=None, min_length=1)

    @field_validator("title", "description", "requirements")
    @classmethod
    def strip_not_blank(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return _require_stripped(value)


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
    public_slug: str
    public_url: str
    status: JobStatus
    created_at: datetime
    closed_at: datetime | None


class JobDetailResponse(JobResponse):
    application_counts: ApplicationCounts


class PublicJobResponse(BaseModel):
    title: str
    description: str
    requirements: str
    status: JobStatus
