from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


def _require_stripped(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        raise ValueError("must not be blank")
    return stripped


class RegisterRequest(BaseModel):
    company_name: str = Field(min_length=1, max_length=200)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("company_name")
    @classmethod
    def strip_company_name(cls, value: str) -> str:
        return _require_stripped(value)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=1)


class RecruiterMeResponse(BaseModel):
    id: UUID
    company_name: str
    email: str


class AuthResponse(RecruiterMeResponse):
    access_token: str
    refresh_token: str
