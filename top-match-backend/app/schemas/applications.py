from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.models import ApplicationStatus


class ApplicationCreate(BaseModel):
    email: EmailStr
    file_id: UUID


class ResumeUploaded(BaseModel):
    id: UUID


class ApplicationAccepted(BaseModel):
    id: UUID
    status: ApplicationStatus
