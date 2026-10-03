from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.models import ApplicationStatus
from app.schemas.evaluation import Citation
from app.schemas.jobs import ApplicationCounts


class ApplicationCreate(BaseModel):
    email: EmailStr
    file_id: UUID
    consented: Literal[True]


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
