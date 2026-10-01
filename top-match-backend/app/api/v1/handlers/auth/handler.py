from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Recruiter
from app.schemas.auth import AuthResponse, RecruiterMeResponse, RegisterRequest
from app.services import auth as auth_service


async def register(db: AsyncSession, body: RegisterRequest) -> AuthResponse:
    issued = await auth_service.register(
        db,
        company_name=body.company_name,
        email=str(body.email),
        password=body.password,
    )
    return auth_service.to_auth_response(issued)


async def login(db: AsyncSession, email: str, password: str) -> AuthResponse:
    issued = await auth_service.login(db, email=email, password=password)
    return auth_service.to_auth_response(issued)


async def refresh(db: AsyncSession, refresh_token: str) -> AuthResponse:
    issued = await auth_service.refresh(db, refresh_token)
    return auth_service.to_auth_response(issued)


async def logout(db: AsyncSession, refresh_token: str) -> None:
    await auth_service.logout(db, refresh_token)


async def me(recruiter: Recruiter) -> RecruiterMeResponse:
    return auth_service.to_me_response(recruiter)
