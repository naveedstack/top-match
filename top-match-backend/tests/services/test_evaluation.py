from dataclasses import dataclass
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EvaluationFailedError
from app.integrations.llm import GeminiEvaluationCompleter, LLMCompletion
from app.models import Application, ApplicationStatus, Evaluation, Job, JobStatus, Recruiter
from app.prompts.evaluation import PROMPT_VERSION
from app.repositories import evaluations as evaluations_repo
from app.schemas.evaluation import Citation, EvaluationResult, ModelEvaluation
from app.services.evaluation import evaluate, save_evaluation

RESUME = (
    "Senior software engineer with eight years of Python. "
    "Built production HTTP APIs in FastAPI. "
    "Designed PostgreSQL schemas for high-volume applications."
)

QUOTE = "Built production HTTP APIs in FastAPI."


@dataclass
class DummyJob:
    title: str = "Senior Backend Engineer"
    description: str = "Build the screening API."
    requirements: str = "Python, FastAPI, PostgreSQL"


class FakeCompleter:
    def __init__(self, evaluation: ModelEvaluation) -> None:
        self.evaluation = evaluation
        self.calls = 0

    async def complete(self, job: DummyJob, resume_text: str) -> LLMCompletion:
        self.calls += 1
        return LLMCompletion(
            evaluation=self.evaluation,
            model_name="fake-model",
            latency_ms=12,
            input_tokens=8,
            output_tokens=4,
        )


def _resume_evaluation(**overrides: object) -> ModelEvaluation:
    body: dict[str, object] = {
        "is_resume": True,
        "refusal_reason": None,
        "score": 88,
        "key_strengths": ["FastAPI production APIs"],
        "missing_requirements": [],
        "citations": [Citation(claim="Uses FastAPI", quote=QUOTE)],
        "injection_suspected": False,
    }
    body.update(overrides)
    return ModelEvaluation.model_validate(body)


async def test_citation_matches_whitespace_and_case() -> None:
    evaluation = _resume_evaluation(
        citations=[
            Citation(claim="Uses FastAPI", quote="  built   PRODUCTION http apis in fastapi.  ")
        ]
    )
    result = await evaluate(DummyJob(), RESUME, completer=FakeCompleter(evaluation))

    assert len(result.citations) == 1
    assert result.needs_review is False


async def test_invented_quotes_are_dropped_and_flagged() -> None:
    evaluation = _resume_evaluation(
        citations=[
            Citation(claim="Uses FastAPI", quote=QUOTE),
            Citation(claim="Rust expert", quote="Rewrote the kernel in Rust"),
            Citation(claim="Go microservices", quote="Led a Go platform rewrite"),
        ]
    )
    result = await evaluate(DummyJob(), RESUME, completer=FakeCompleter(evaluation))

    assert result.citations_submitted == 3
    assert result.citations == [Citation(claim="Uses FastAPI", quote=QUOTE)]
    assert result.needs_review is True


async def test_empty_text_refuses_without_llm() -> None:
    fake = FakeCompleter(_resume_evaluation())
    result = await evaluate(DummyJob(), "too short", completer=fake)

    assert fake.calls == 0
    assert result.is_resume is False
    assert result.score is None
    assert result.refusal_reason is not None
    assert result.prompt_version == PROMPT_VERSION


async def test_non_resume_has_no_score() -> None:
    evaluation = ModelEvaluation(
        is_resume=False,
        refusal_reason="This is a restaurant menu",
        score=91,
        key_strengths=["Should be dropped"],
        missing_requirements=["Should be dropped"],
        citations=[Citation(claim="ignored", quote=QUOTE)],
        injection_suspected=False,
    )
    result = await evaluate(DummyJob(), RESUME, completer=FakeCompleter(evaluation))

    assert result.is_resume is False
    assert result.score is None
    assert result.key_strengths == []
    assert result.missing_requirements == []
    assert result.citations == []
    assert result.citations_submitted == 1
    assert result.refusal_reason == "This is a restaurant menu"


async def test_injection_caps_score_and_flags_review() -> None:
    evaluation = _resume_evaluation(score=97, injection_suspected=True)
    result = await evaluate(DummyJob(), RESUME, completer=FakeCompleter(evaluation))

    assert result.score == 40
    assert result.injection_suspected is True
    assert result.needs_review is True


async def test_retries_then_succeeds() -> None:
    calls = {"n": 0}

    async def fail_twice(_human: str) -> tuple[ModelEvaluation, SimpleNamespace]:
        calls["n"] += 1
        if calls["n"] < 3:
            raise TimeoutError("transient")
        return (
            _resume_evaluation(),
            SimpleNamespace(usage_metadata={"input_tokens": 3, "output_tokens": 2}),
        )

    completion = await GeminiEvaluationCompleter(invoke=fail_twice).complete(DummyJob(), RESUME)

    assert calls["n"] == 3
    assert completion.evaluation.score == 88
    assert completion.input_tokens == 3
    assert completion.output_tokens == 2


async def test_third_failure_raises_evaluation_failed() -> None:
    calls = {"n": 0}

    async def always_fail(_human: str) -> tuple[ModelEvaluation, SimpleNamespace]:
        calls["n"] += 1
        raise TimeoutError("still down")

    with pytest.raises(EvaluationFailedError):
        await GeminiEvaluationCompleter(invoke=always_fail).complete(DummyJob(), RESUME)

    assert calls["n"] == 3


async def test_save_evaluation_round_trips_jsonb(
    db_session: AsyncSession, recruiter: Recruiter
) -> None:
    job = Job(
        recruiter_id=recruiter.id,
        title="Senior Backend Engineer",
        description="Build APIs",
        requirements="Python, FastAPI, PostgreSQL",
        public_slug=uuid4().hex[:12],
        status=JobStatus.OPEN,
    )
    db_session.add(job)
    await db_session.flush()
    application = Application(
        job_id=job.id,
        email="candidate@example.com",
        status=ApplicationStatus.RECEIVED,
    )
    db_session.add(application)
    await db_session.flush()

    result = EvaluationResult(
        is_resume=True,
        refusal_reason=None,
        score=88,
        key_strengths=["FastAPI production APIs"],
        missing_requirements=["Redis"],
        citations=[Citation(claim="Uses FastAPI", quote=QUOTE)],
        injection_suspected=False,
        needs_review=False,
        citations_submitted=1,
        model_name="fake-model",
        prompt_version=PROMPT_VERSION,
        latency_ms=12,
        input_tokens=8,
        output_tokens=4,
    )
    saved = await save_evaluation(db_session, application.id, result)
    loaded = await evaluations_repo.get_by_application_id(db_session, application.id)

    assert loaded is not None
    assert loaded.id == saved.id
    assert loaded.score == 88
    assert loaded.key_strengths == ["FastAPI production APIs"]
    assert loaded.missing_requirements == ["Redis"]
    assert loaded.citations == [{"claim": "Uses FastAPI", "quote": QUOTE}]
    assert loaded.is_resume is True
    assert loaded.needs_review is False
    assert isinstance(loaded, Evaluation)
