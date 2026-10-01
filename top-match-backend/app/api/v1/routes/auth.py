from fastapi import APIRouter, Request, Response, status

from app.api.deps import CurrentRecruiter, DbSession
from app.api.v1.handlers.auth import handler as auth_handlers
from app.core.rate_limit import limiter
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    RecruiterMeResponse,
    RefreshRequest,
    RegisterRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request, response: Response, body: RegisterRequest, db: DbSession
) -> AuthResponse:
    return await auth_handlers.register(db, body)


@router.post("/login")
@limiter.limit("5/minute")
async def login(
    request: Request, response: Response, body: LoginRequest, db: DbSession
) -> AuthResponse:
    return await auth_handlers.login(db, str(body.email), body.password)


@router.post("/refresh")
async def refresh(body: RefreshRequest, db: DbSession) -> AuthResponse:
    return await auth_handlers.refresh(db, body.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: RefreshRequest, db: DbSession) -> None:
    await auth_handlers.logout(db, body.refresh_token)


@router.get("/me")
async def me(recruiter: CurrentRecruiter) -> RecruiterMeResponse:
    return await auth_handlers.me(recruiter)
