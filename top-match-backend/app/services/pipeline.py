"""Screening runner: accept -> knockout -> answers -> resume.

Each phase returns a PhaseRun and never touches the database. The runner records every run
and is the only code that moves an application between screening states.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import EvaluationFailedError, InvalidResumeError
from app.db.session import SessionLocal
from app.integrations import storage
from app.integrations.llm import EvaluationCompleter, JobLike
from app.models import (
    PHASE_ORDER,
    Application,
    ApplicationStatus,
    PhaseOutcome,
    PhaseResult,
    ReasonCode,
    ScreeningPhase,
)
from app.repositories import applications as applications_repo
from app.repositories import evaluations as evaluations_repo
from app.repositories import phase_results as phase_results_repo
from app.schemas.evaluation import EvaluationResult
from app.schemas.forms import parse_form_fields
from app.services import evaluation as evaluation_service
from app.services import screening
from app.services.ingestion import extract_text
from app.services.redaction import redact_resume

logger = logging.getLogger(__name__)

_llm_semaphore: asyncio.Semaphore | None = None


def _semaphore() -> asyncio.Semaphore:
    global _llm_semaphore
    if _llm_semaphore is None:
        _llm_semaphore = asyncio.Semaphore(settings.LLM_MAX_CONCURRENCY)
    return _llm_semaphore


@dataclass(frozen=True)
class Reason:
    code: ReasonCode
    message: str
    field_id: UUID | None = None

    def dump(self) -> dict[str, Any]:
        data: dict[str, Any] = {"code": self.code.value, "message": self.message}
        if self.field_id is not None:
            data["field_id"] = str(self.field_id)
        return data


@dataclass(frozen=True)
class PhaseRun:
    phase: ScreeningPhase
    outcome: PhaseOutcome
    reasons: tuple[Reason, ...] = ()
    evidence: dict[str, Any] = field(default_factory=dict)
    config_version: str | None = None
    # Terminal status for the application; None means the run continues.
    status: ApplicationStatus | None = None
    evaluation: EvaluationResult | None = None
    extracted_text: str | None = None

    @property
    def stopped(self) -> bool:
        return self.outcome in (PhaseOutcome.FAIL, PhaseOutcome.ERROR)


@dataclass
class _JobSnapshot:
    """Job fields the resume phase needs once the session is closed."""

    title: str
    description: str
    requirements: str


def phase_after(phase: ScreeningPhase | None) -> ScreeningPhase | None:
    if phase is None:
        return PHASE_ORDER[0]
    index = PHASE_ORDER.index(phase)
    return PHASE_ORDER[index + 1] if index + 1 < len(PHASE_ORDER) else None


def phase_before(phase: ScreeningPhase) -> ScreeningPhase | None:
    index = PHASE_ORDER.index(phase)
    return PHASE_ORDER[index - 1] if index > 0 else None


def restart_after(application: Application, phase: ScreeningPhase | None) -> None:
    """Queue the application to run again from the phase after `phase`."""
    application.status = ApplicationStatus.PROCESSING
    application.current_phase = phase
    application.stopped_phase = None
    application.stop_code = None
    application.stop_reason = None
    application.reviewed_at = None
    application.score = None
    application.processing_started_at = datetime.now(UTC)


# --- phases ---------------------------------------------------------------------------


def _error(phase: ScreeningPhase, code: ReasonCode, message: str) -> PhaseRun:
    return PhaseRun(
        phase,
        PhaseOutcome.ERROR,
        reasons=(Reason(code, message),),
        status=ApplicationStatus.FAILED,
    )


async def _accept(application: Application) -> PhaseRun:
    key = application.resume_storage_key
    if key is None or not await storage.exists(key):
        return _error(ScreeningPhase.ACCEPT, ReasonCode.MISSING_FILE, "Resume file is missing")
    return PhaseRun(ScreeningPhase.ACCEPT, PhaseOutcome.PASS)


async def _knockout(application: Application) -> PhaseRun:
    fields = parse_form_fields(application.job.form_fields)
    version = screening.config_version(application.job.form_fields)
    if not screening.has_knockouts(fields):
        return PhaseRun(ScreeningPhase.KNOCKOUT, PhaseOutcome.SKIPPED, config_version=version)
    failures = screening.evaluate_knockouts(fields, application.answers or {})
    if not failures:
        return PhaseRun(ScreeningPhase.KNOCKOUT, PhaseOutcome.PASS, config_version=version)
    return PhaseRun(
        ScreeningPhase.KNOCKOUT,
        PhaseOutcome.FAIL,
        reasons=tuple(
            Reason(ReasonCode.KNOCKOUT_FAILED, item.reason, item.field_id) for item in failures
        ),
        config_version=version,
        status=ApplicationStatus.KNOCKED_OUT,
    )


async def _answers(application: Application) -> PhaseRun:
    fields = parse_form_fields(application.job.form_fields)
    scored = screening.score_answers(fields, application.answers or {})
    version = screening.config_version(application.job.form_fields)
    if scored is None:
        return PhaseRun(ScreeningPhase.ANSWERS, PhaseOutcome.SKIPPED, config_version=version)
    return PhaseRun(
        ScreeningPhase.ANSWERS,
        PhaseOutcome.PASS,
        evidence={"answers_score": scored.score, "fields": scored.breakdown},
        config_version=version,
    )


_CODE_PHASES: dict[ScreeningPhase, Callable[[Application], Awaitable[PhaseRun]]] = {
    ScreeningPhase.ACCEPT: _accept,
    ScreeningPhase.KNOCKOUT: _knockout,
    ScreeningPhase.ANSWERS: _answers,
}


async def _resume(
    application_id: UUID,
    storage_key: str,
    job: JobLike,
    completer: EvaluationCompleter | None,
) -> PhaseRun:
    """OCR the page images, redact personal details and ask the model. No open session.

    The model sees and quotes are verified against the redacted text; the original text is
    kept for the recruiter. Only the number of removed lines is recorded.
    """
    phase = ScreeningPhase.RESUME
    unreadable = "Resume text could not be read"
    try:
        ingestion = await extract_text(await storage.get(storage_key))
    except (InvalidResumeError, OSError, ValueError) as exc:
        _log_failure("ingestion", application_id, exc)
        return _error(phase, ReasonCode.UNREADABLE, unreadable)
    if ingestion.too_empty:
        return _error(phase, ReasonCode.UNREADABLE, unreadable)

    redaction = redact_resume(ingestion.text)
    redaction_evidence = {"redacted_lines": redaction.removed_lines}
    try:
        async with _semaphore():
            result = await evaluation_service.evaluate(job, redaction.text, completer=completer)
    except EvaluationFailedError as exc:
        _log_failure("evaluation", application_id, exc)
        run = _error(phase, ReasonCode.SCORING_FAILED, "Scoring failed")
        return replace(run, evidence=redaction_evidence, extracted_text=ingestion.text)

    version = screening.config_version(
        {"description": job.description, "requirements": job.requirements}
    )
    if not result.is_resume:
        return PhaseRun(
            phase,
            PhaseOutcome.FAIL,
            reasons=(Reason(ReasonCode.NOT_RESUME, result.refusal_reason or "Not a resume"),),
            evidence=redaction_evidence,
            config_version=version,
            status=ApplicationStatus.REFUSED,
            evaluation=result,
            extracted_text=ingestion.text,
        )
    return PhaseRun(
        phase,
        PhaseOutcome.REVIEW if result.needs_review else PhaseOutcome.PASS,
        evidence={"score": result.score, **redaction_evidence},
        config_version=version,
        status=ApplicationStatus.SCORED,
        evaluation=result,
        extracted_text=ingestion.text,
    )


def _log_failure(stage: str, application_id: UUID, exc: BaseException) -> None:
    # Exception text can carry resume or model output, so only the type is logged (Rule 4).
    logger.warning(
        "resume phase failed stage=%s application_id=%s error=%s",
        stage,
        application_id,
        type(exc).__name__,
    )


# --- runner ---------------------------------------------------------------------------


@asynccontextmanager
async def _scope(session: AsyncSession | None) -> AsyncIterator[AsyncSession]:
    """Use the caller's session, or a short-lived one so no connection is held during OCR/LLM."""
    if session is not None:
        yield session
        return
    async with SessionLocal() as owned:
        yield owned


async def _load(session: AsyncSession, application_id: UUID) -> Application | None:
    application = await applications_repo.get_by_id(session, application_id, populate_existing=True)
    if application is None or application.job is None:
        return None
    return application


async def _record(session: AsyncSession, application: Application, run: PhaseRun) -> None:
    """Write the phase_results row and move the application's state in one commit."""
    result = run.evaluation
    await phase_results_repo.add(
        session,
        PhaseResult(
            application_id=application.id,
            phase=run.phase,
            outcome=run.outcome,
            reasons=[reason.dump() for reason in run.reasons],
            evidence=run.evidence,
            config_version=run.config_version,
            model_name=None if result is None else result.model_name or None,
            prompt_version=None if result is None else result.prompt_version,
            input_tokens=None if result is None else result.input_tokens,
            output_tokens=None if result is None else result.output_tokens,
            latency_ms=None if result is None else result.latency_ms,
        ),
    )
    if run.extracted_text is not None:
        application.extracted_text = run.extracted_text
    if result is not None:
        await evaluations_repo.delete_by_application_id(session, application.id)
        await evaluation_service.save_evaluation(session, application.id, result, commit=False)
        application.score = result.score
    application.current_phase = run.phase
    if run.stopped:
        application.stopped_phase = run.phase
        application.stop_code = run.reasons[0].code.value if run.reasons else None
        application.stop_reason = "; ".join(reason.message for reason in run.reasons) or None
    if run.status is not None:
        application.status = run.status
    else:
        # Still running: refresh the clock the stuck sweep uses.
        application.processing_started_at = datetime.now(UTC)
    await session.commit()


async def process_application(
    application_id: UUID,
    session: AsyncSession | None = None,
    *,
    reclaim_processing: bool = False,
    completer: EvaluationCompleter | None = None,
) -> None:
    """Run the remaining phases in order, resuming after `current_phase`."""
    async with _scope(session) as active:
        if not await applications_repo.claim_for_processing(
            active, application_id, reclaim_processing=reclaim_processing
        ):
            return
        application = await _load(active, application_id)
        if application is None:
            return
        start = phase_after(application.current_phase)
        if start is None:
            # Nothing left to run; only reachable if state was edited by hand.
            run = _error(ScreeningPhase.RESUME, ReasonCode.SCORING_FAILED, "Nothing left to run")
            await _record(active, application, run)
            return
        for phase in PHASE_ORDER[PHASE_ORDER.index(start) :]:
            runner = _CODE_PHASES.get(phase)
            if runner is None:
                continue
            run = await runner(application)
            await _record(active, application, run)
            if run.stopped:
                return
        storage_key = application.resume_storage_key
        job = _JobSnapshot(
            application.job.title, application.job.description, application.job.requirements
        )

    if storage_key is None:
        run = _error(ScreeningPhase.RESUME, ReasonCode.MISSING_FILE, "Resume file is missing")
    else:
        run = await _resume(application_id, storage_key, job, completer)
    async with _scope(session) as active:
        application = await _load(active, application_id)
        if application is not None:
            await _record(active, application, run)


async def recover_stuck_applications(
    session: AsyncSession | None = None,
    *,
    completer: EvaluationCompleter | None = None,
) -> list[UUID]:
    cutoff = datetime.now(UTC) - timedelta(minutes=settings.STUCK_APPLICATION_MINUTES)

    async def _run(active: AsyncSession) -> list[UUID]:
        ids = await applications_repo.list_stuck_ids(active, cutoff)
        for application_id in ids:
            await process_application(
                application_id, active, reclaim_processing=True, completer=completer
            )
        return ids

    if session is not None:
        return await _run(session)
    async with SessionLocal() as owned:
        return await _run(owned)
