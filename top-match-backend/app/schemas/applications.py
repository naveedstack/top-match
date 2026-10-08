from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.models import ApplicationStatus, PhaseOutcome, ScreeningPhase
from app.schemas.conditions import ConditionVerdict, JobCondition
from app.schemas.evaluation import Citation
from app.schemas.jobs import ApplicationCounts


class ApplicationCreate(BaseModel):
    email: EmailStr
    file_id: UUID
    consented: Literal[True]
    answers: dict[str, Any] = Field(default_factory=dict)


class AttachmentUploadUrlRequest(BaseModel):
    field_id: UUID
    filename: str = Field(min_length=1, max_length=255)
    content_type: str
    byte_size: int = Field(ge=1)


class ApplicationAnswerItem(BaseModel):
    field_id: UUID
    label: str
    type: Literal["text", "number", "dropdown", "radio", "checkboxes", "file"]
    value: str | float | list[str] | None = None
    filename: str | None = None
    download_url: str | None = None
    condition: JobCondition | None = None
    condition_verdict: ConditionVerdict | None = None


class ResumeUploaded(BaseModel):
    id: UUID


class UploadUrlRequest(BaseModel):
    content_type: str
    byte_size: int = Field(ge=1)


class UploadUrlResponse(BaseModel):
    file_id: UUID
    upload_url: str
    headers: dict[str, str]
    expires_at: datetime


class ApplicationAccepted(BaseModel):
    id: UUID
    status: ApplicationStatus


class LeaderboardItem(BaseModel):
    id: UUID
    email: str
    status: ApplicationStatus
    score: int | None
    needs_review: bool
    created_at: datetime
    current_phase: ScreeningPhase | None
    stopped_phase: ScreeningPhase | None
    stop_code: str | None
    stop_reason: str | None
    reviewed_at: datetime | None


class PhaseResultItem(BaseModel):
    phase: ScreeningPhase
    outcome: PhaseOutcome
    reasons: list[dict[str, Any]]
    overridden: bool
    created_at: datetime


class LeaderboardResponse(BaseModel):
    items: list[LeaderboardItem]
    counts: ApplicationCounts
    total: int
    screening_disclaimer: str


class ApplicationDetailResponse(BaseModel):
    id: UUID
    email: str
    status: ApplicationStatus
    score: int | None
    created_at: datetime
    is_resume: bool | None
    refusal_reason: str | None
    key_strengths: list[str]
    missing_requirements: list[str]
    citations: list[Citation]
    injection_suspected: bool | None
    needs_review: bool | None
    resume_url: str | None
    answers: list[ApplicationAnswerItem]
    current_phase: ScreeningPhase | None
    stopped_phase: ScreeningPhase | None
    stop_code: str | None
    stop_reason: str | None
    reviewed_at: datetime | None
    answers_score: int | None
    phase_results: list[PhaseResultItem]


class ExportRequest(BaseModel):
    application_ids: list[UUID] | None = None
    top_n: int | None = Field(default=None, ge=1, le=500)

    @model_validator(mode="after")
    def require_one_selector(self) -> ExportRequest:
        has_ids = bool(self.application_ids)
        has_top = self.top_n is not None
        if has_ids == has_top:
            raise ValueError("Provide either application_ids or top_n")
        return self
