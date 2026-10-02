from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.integrations.llm import EvaluationCompleter, JobLike, LLMCompletion, get_completer
from app.models import Evaluation
from app.prompts.evaluation import PROMPT_VERSION
from app.repositories import evaluations as evaluations_repo
from app.schemas.evaluation import Citation, EvaluationResult
from app.services.ingestion import EMPTY_CHAR_THRESHOLD

_INJECTION_SCORE_CAP = 40
_EMPTY_REFUSAL = "Extracted text is too short to be a resume"


def _normalize_for_match(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def verify_citations(resume_text: str, citations: list[Citation]) -> list[Citation]:
    haystack = _normalize_for_match(resume_text)
    verified: list[Citation] = []
    for citation in citations:
        quote = _normalize_for_match(citation.quote)
        if quote and quote in haystack:
            verified.append(citation)
    return verified


def _needs_review(
    *,
    is_resume: bool,
    injection_suspected: bool,
    citations_submitted: int,
    citations_verified: int,
) -> bool:
    if injection_suspected:
        return True
    if not is_resume:
        return False
    if citations_submitted == 0 or citations_verified == 0:
        return True
    return citations_verified / citations_submitted < 0.5


def _empty_refusal() -> EvaluationResult:
    return EvaluationResult(
        is_resume=False,
        refusal_reason=_EMPTY_REFUSAL,
        score=None,
        key_strengths=[],
        missing_requirements=[],
        citations=[],
        injection_suspected=False,
        needs_review=False,
        citations_submitted=0,
        model_name="",
        prompt_version=PROMPT_VERSION,
        latency_ms=0,
        input_tokens=None,
        output_tokens=None,
    )


def _from_completion(completion: LLMCompletion, resume_text: str) -> EvaluationResult:
    model = completion.evaluation
    submitted = list(model.citations)
    if not model.is_resume:
        score = None
        strengths: list[str] = []
        missing: list[str] = []
        citations: list[Citation] = []
    else:
        score = model.score
        strengths = list(model.key_strengths)
        missing = list(model.missing_requirements)
        citations = verify_citations(resume_text, submitted)
        if model.injection_suspected and score is not None:
            score = min(score, _INJECTION_SCORE_CAP)
    return EvaluationResult(
        is_resume=model.is_resume,
        refusal_reason=None if model.is_resume else model.refusal_reason,
        score=score,
        key_strengths=strengths,
        missing_requirements=missing,
        citations=citations,
        injection_suspected=model.injection_suspected,
        needs_review=_needs_review(
            is_resume=model.is_resume,
            injection_suspected=model.injection_suspected,
            citations_submitted=len(submitted),
            citations_verified=len(citations),
        ),
        citations_submitted=len(submitted),
        model_name=completion.model_name,
        prompt_version=PROMPT_VERSION,
        latency_ms=completion.latency_ms,
        input_tokens=completion.input_tokens,
        output_tokens=completion.output_tokens,
    )


async def evaluate(
    job: JobLike,
    resume_text: str,
    *,
    completer: EvaluationCompleter | None = None,
) -> EvaluationResult:
    if len(resume_text.strip()) < EMPTY_CHAR_THRESHOLD:
        return _empty_refusal()
    active = completer or get_completer()
    completion = await active.complete(job, resume_text)
    return _from_completion(completion, resume_text)


async def save_evaluation(
    session: AsyncSession, application_id: UUID, result: EvaluationResult, *, commit: bool = True
) -> Evaluation:
    record = Evaluation(
        application_id=application_id,
        score=result.score,
        key_strengths=list(result.key_strengths),
        missing_requirements=list(result.missing_requirements),
        citations=[citation.model_dump() for citation in result.citations],
        is_resume=result.is_resume,
        refusal_reason=result.refusal_reason,
        injection_suspected=result.injection_suspected,
        needs_review=result.needs_review,
        model_name=result.model_name or settings.GEMINI_MODEL,
        prompt_version=result.prompt_version,
        latency_ms=result.latency_ms,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
    )
    await evaluations_repo.add(session, record)
    if commit:
        await session.commit()
        await session.refresh(record)
    else:
        await session.flush()
    return record
