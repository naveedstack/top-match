from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import (
    DuplicateApplicationError,
    DuplicateEmailError,
    InvalidCredentialsError,
    InvalidResumeError,
    InvalidTokenError,
    JobClosedError,
    JobNotFoundError,
    ResumeAlreadyUsedError,
    ResumeNotFoundError,
    ResumeTooLargeError,
)
from app.core.logging import configure_logging
from app.core.rate_limit import limiter
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    configure_logging()

    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
    )
    app.state.limiter = limiter
    app.add_middleware(SlowAPIMiddleware)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(DuplicateEmailError)
    async def duplicate_email_handler(request: Request, exc: DuplicateEmailError) -> JSONResponse:
        return JSONResponse(status_code=409, content={"detail": "Email already registered"})

    @app.exception_handler(InvalidCredentialsError)
    async def invalid_credentials_handler(
        request: Request, exc: InvalidCredentialsError
    ) -> JSONResponse:
        return JSONResponse(status_code=401, content={"detail": "Invalid email or password"})

    @app.exception_handler(InvalidTokenError)
    async def invalid_token_handler(request: Request, exc: InvalidTokenError) -> JSONResponse:
        return JSONResponse(status_code=401, content={"detail": "Authentication required"})

    @app.exception_handler(JobNotFoundError)
    async def job_not_found_handler(request: Request, exc: JobNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "Job not found"})

    @app.exception_handler(JobClosedError)
    async def job_closed_handler(request: Request, exc: JobClosedError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"detail": "This job is no longer accepting applications"},
        )

    @app.exception_handler(DuplicateApplicationError)
    async def duplicate_application_handler(
        request: Request, exc: DuplicateApplicationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"detail": "An application with this email already exists for this job"},
        )

    @app.exception_handler(ResumeNotFoundError)
    async def resume_not_found_handler(request: Request, exc: ResumeNotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "Resume file not found"})

    @app.exception_handler(ResumeAlreadyUsedError)
    async def resume_already_used_handler(
        request: Request, exc: ResumeAlreadyUsedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"detail": "This resume file was already used on an application"},
        )

    @app.exception_handler(ResumeTooLargeError)
    async def resume_too_large_handler(request: Request, exc: ResumeTooLargeError) -> JSONResponse:
        return JSONResponse(
            status_code=413,
            content={"detail": "Resume exceeds the maximum allowed size"},
        )

    @app.exception_handler(InvalidResumeError)
    async def invalid_resume_handler(request: Request, exc: InvalidResumeError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": exc.message})

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        return JSONResponse(status_code=429, content={"detail": "Too many requests"})

    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_app()
