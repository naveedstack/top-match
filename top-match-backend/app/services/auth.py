import asyncio
from dataclasses import dataclass

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.email import normalize_email
from app.core.exceptions import DuplicateEmailError, InvalidCredentialsError, InvalidTokenError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    dummy_verify_password,
    hash_password,
    verify_password,
)
from app.core.slugs import numbered_slug, reserved_or_base_slug
from app.models import Recruiter
from app.repositories import recruiters as recruiters_repo
from app.schemas.auth import AuthResponse, RecruiterMeResponse


@dataclass(frozen=True)
class IssuedAuth:
    recruiter: Recruiter
    access_token: str
    refresh_token: str


def to_me_response(recruiter: Recruiter) -> RecruiterMeResponse:
    return RecruiterMeResponse(
        id=recruiter.id,
        company_name=recruiter.company_name,
        company_slug=recruiter.company_slug,
        email=recruiter.email,
    )


def to_auth_response(issued: IssuedAuth) -> AuthResponse:
    return AuthResponse(
        **to_me_response(issued.recruiter).model_dump(),
        access_token=issued.access_token,
        refresh_token=issued.refresh_token,
    )


async def _issue_tokens(session: AsyncSession, recruiter: Recruiter) -> IssuedAuth:
    access_token = create_access_token(recruiter.id)
    jti, refresh_token, expires_at = create_refresh_token(recruiter.id)
    await recruiters_repo.add_refresh_token(
        session,
        recruiter_id=recruiter.id,
        jti=jti,
        expires_at=expires_at,
    )
    return IssuedAuth(
        recruiter=recruiter,
        access_token=access_token,
        refresh_token=refresh_token,
    )


async def unique_company_slug(session: AsyncSession, company_name: str) -> str:
    base = reserved_or_base_slug(company_name)
    n = 1
    while n <= 1000:
        candidate = numbered_slug(base, n)
        if await recruiters_repo.get_by_company_slug(session, candidate) is None:
            return candidate
        n += 1
    raise RuntimeError("Could not generate a unique company slug")


async def register(
    session: AsyncSession, *, company_name: str, email: str, password: str
) -> IssuedAuth:
    normalized = normalize_email(email)
    if await recruiters_repo.get_by_email(session, normalized) is not None:
        raise DuplicateEmailError
    password_hash = await asyncio.to_thread(hash_password, password)
    company_slug = await unique_company_slug(session, company_name)
    try:
        recruiter = await recruiters_repo.create(
            session,
            email=normalized,
            name=company_name,
            company_name=company_name,
            company_slug=company_slug,
            password_hash=password_hash,
        )
        issued = await _issue_tokens(session, recruiter)
        await session.commit()
        await session.refresh(recruiter)
    except IntegrityError:
        await session.rollback()
        raise DuplicateEmailError from None
    return issued


async def login(session: AsyncSession, *, email: str, password: str) -> IssuedAuth:
    normalized = normalize_email(email)
    recruiter = await recruiters_repo.get_by_email(session, normalized)
    if recruiter is None:
        await asyncio.to_thread(dummy_verify_password, password)
        raise InvalidCredentialsError
    if not await asyncio.to_thread(verify_password, password, recruiter.password_hash):
        raise InvalidCredentialsError
    issued = await _issue_tokens(session, recruiter)
    await session.commit()
    return issued


async def refresh(session: AsyncSession, refresh_token: str) -> IssuedAuth:
    recruiter_id, jti = decode_refresh_token(refresh_token)
    if not await recruiters_repo.revoke_active_refresh_token(session, jti):
        raise InvalidTokenError
    recruiter = await recruiters_repo.get_by_id(session, recruiter_id)
    if recruiter is None:
        raise InvalidTokenError
    issued = await _issue_tokens(session, recruiter)
    await session.commit()
    return issued


async def logout(session: AsyncSession, refresh_token: str) -> None:
    _, jti = decode_refresh_token(refresh_token)
    await recruiters_repo.revoke_active_refresh_token(session, jti)
    await session.commit()
