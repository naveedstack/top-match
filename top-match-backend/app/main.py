import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import (
    ApplicationNotFoundError,
    AttachmentAlreadyUsedError,
    AttachmentNotFoundError,
    DuplicateApplicationError,
    DuplicateEmailError,
    FormAnswersError,
    FormLockedError,
    InvalidCredentialsError,
    InvalidTokenError,
    InvalidUploadError,
    JobClosedError,
    JobNotFoundError,
    ResumeAlreadyUsedError,
    ResumeNotFoundError,
    ResumeTooLargeError,
)
from app.core.logging import configure_logging
from app.core.rate_limit import limiter
from app.core.request_id import RequestIdMiddleware
from app.db.session import engine
from app.services import screening_queue
from app.services.pipeline import recover_stuck_applications
from app.services.retention import purge_expired_applications

logger = logging.getLogger(__name__)


def _require_gemini_data_use() -> None:
    if settings.ENVIRONMENT != "local" and not settings.GEMINI_DATA_USE_ACKNOWLEDGED:
        raise RuntimeError(
            "GEMINI_DATA_USE_ACKNOWLEDGED must be true when ENVIRONMENT is not local. "
            "Use paid-tier Gemini or Vertex AI; free-tier Gemini may train on resume content."
        )


async def _stuck_loop(stop: asyncio.Event) -> None:
    while not stop.is_set():
        if settings.PIPELINE_ENABLED:
            try:
                await recover_stuck_applications()
            except Exception:
                logger.exception("stuck application sweep failed")
        try:
            await asyncio.wait_for(stop.wait(), timeout=60)
        except TimeoutError:
            continue


async def _retention_loop(stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            await purge_expired_applications()
        except Exception:
            logger.exception("retention sweep failed")
        try:
            await asyncio.wait_for(stop.wait(), timeout=3600)
        except TimeoutError:
            continue


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    stop = asyncio.Event()
    sweep = asyncio.create_task(_stuck_loop(stop))
    retention = asyncio.create_task(_retention_loop(stop))
    yield
    stop.set()
    sweep.cancel()
    retention.cancel()
    with suppress(asyncio.CancelledError):
        await sweep
    with suppress(asyncio.CancelledError):
        await retention
    await screening_queue.drain()
    await engine.dispose()


def create_app() -> FastAPI:
    _require_gemini_data_use()
    configure_logging()
    docs_enabled = settings.ENVIRONMENT == "local"

    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json" if docs_enabled else None,
        docs_url="/docs" if docs_enabled else None,
        redoc_url="/redoc" if docs_enabled else None,
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
    app.add_middleware(RequestIdMiddleware)

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

    @app.exception_handler(ApplicationNotFoundError)
    async def application_not_found_handler(
        request: Request, exc: ApplicationNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "Application not found"})

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
            content={"detail": "File exceeds the maximum allowed size"},
        )

    @app.exception_handler(InvalidUploadError)
    async def invalid_upload_handler(request: Request, exc: InvalidUploadError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": exc.message})

    @app.exception_handler(FormLockedError)
    async def form_locked_handler(request: Request, exc: FormLockedError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"detail": "The application form cannot be changed after candidates apply"},
        )

    @app.exception_handler(FormAnswersError)
    async def form_answers_handler(request: Request, exc: FormAnswersError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={"detail": "Invalid form answers", "field_errors": exc.field_errors},
        )

    @app.exception_handler(AttachmentNotFoundError)
    async def attachment_not_found_handler(
        request: Request, exc: AttachmentNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": "File not found"})

    @app.exception_handler(AttachmentAlreadyUsedError)
    async def attachment_already_used_handler(
        request: Request, exc: AttachmentAlreadyUsedError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"detail": "This file was already used on an application"},
        )

    @app.exception_handler(RateLimitExceeded)
    async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
        return JSONResponse(status_code=429, content={"detail": "Too many requests"})

    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app


app = create_app()
