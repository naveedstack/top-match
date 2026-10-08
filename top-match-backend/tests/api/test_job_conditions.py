import csv
import io
from typing import Any
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.integrations.llm import JobLike, LLMCompletion
from app.models import ApplicationStatus
from app.repositories import applications as applications_repo
from app.services.ingestion import IngestionResult
from app.services.pipeline import process_application
from app.services.redaction import PLACEHOLDER
from tests.api.test_jobs import JOB_BODY
from tests.api.test_pipeline import RESUME_TEXT, FakeCompleter, _evaluation
from tests.api.test_screening_pipeline import _apply, _job, _phase_rows
from tests.support.conditions import (
    english_condition,
    salary_condition,
    yes_no_condition,
)

PERSONAL_RESUME = f"Date of Birth: 14-08-1995\nCNIC: 35202-1234567-1\n{RESUME_TEXT}"


class RecordingCompleter(FakeCompleter):
    """Fake model client that keeps the resume text it was sent."""

    def __init__(self) -> None:
        super().__init__(_evaluation(80))
        self.sent: list[str] = []

    async def complete(self, job: JobLike, resume_text: str) -> LLMCompletion:
        self.sent.append(resume_text)
        return await super().complete(job, resume_text)


@pytest.fixture(autouse=True)
def fake_ocr(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _extract(_pdf_bytes: bytes) -> IngestionResult:
        return IngestionResult(text=PERSONAL_RESUME, page_count=1, duration_ms=1, too_empty=False)

    monkeypatch.setattr("app.services.pipeline.extract_text", _extract)


def _auth() -> dict[str, Any]:
    return yes_no_condition("work_authorization", "must", "Can you legally work in Pakistan?")


async def _run(db_session: AsyncSession, application_id: UUID) -> RecordingCompleter:
    completer = RecordingCompleter()
    await process_application(application_id, db_session, completer=completer)
    return completer


async def _detail(client: AsyncClient, application_id: UUID) -> dict[str, Any]:
    response = await client.get(f"{settings.API_V1_STR}/applications/{application_id}")
    assert response.status_code == 200
    body: dict[str, Any] = response.json()
    return body


# --- guardrail ------------------------------------------------------------------------


@pytest.mark.parametrize("importance", ["must", "preferred", "info"])
async def test_blocked_condition_is_rejected_at_every_importance(
    client: AsyncClient, importance: str
) -> None:
    field = yes_no_condition("work_authorization", importance, "Are you a Pakistani citizen?")

    response = await client.post(
        f"{settings.API_V1_STR}/jobs", json={**JOB_BODY, "form_fields": [field]}
    )

    assert response.status_code == 422
    [error] = response.json()["guardrail_errors"]
    assert error == {
        "target": field["id"],
        "category": "nationality",
        "message": (
            "Are you a Pakistani citizen? screens on nationality or citizenship, "
            "which is not allowed."
        ),
        "suggestion": "Ask about work authorization instead of nationality.",
    }


async def test_blocked_question_and_requirements_are_rejected(client: AsyncClient) -> None:
    question = {"id": str(uuid4()), "type": "text", "label": "Marital status", "required": False}

    response = await client.post(
        f"{settings.API_V1_STR}/jobs",
        json={**JOB_BODY, "requirements": "Python. Age 25-35.", "form_fields": [question]},
    )

    assert response.status_code == 422
    errors = response.json()["guardrail_errors"]
    assert {(item["target"], item["category"]) for item in errors} == {
        ("requirements", "age"),
        (question["id"], "marital_status"),
    }


async def test_blocked_edit_is_rejected_and_job_unchanged(client: AsyncClient) -> None:
    job = await _job(client, [])

    response = await client.patch(
        f"{settings.API_V1_STR}/jobs/{job['id']}",
        json={"requirements": "Female candidates only", "form_fields": [_auth()]},
    )

    assert response.status_code == 422
    stored = await client.get(f"{settings.API_V1_STR}/jobs/{job['id']}")
    assert stored.json()["requirements"] == JOB_BODY["requirements"]
    assert stored.json()["form_fields"] == []


async def test_work_authorization_condition_is_accepted(client: AsyncClient) -> None:
    job = await _job(client, [_auth()])

    assert job["form_fields"][0]["condition"]["importance"] == "must"
    assert job["form_warnings"] == []


async def test_salary_history_question_warns_but_saves(client: AsyncClient) -> None:
    question = {"id": str(uuid4()), "type": "number", "label": "Current salary", "required": True}

    job = await _job(client, [question])

    assert [item["field_id"] for item in job["form_warnings"]] == [question["id"]]


# --- screening ------------------------------------------------------------------------


async def test_failed_must_condition_never_calls_the_model(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    field = _auth()
    job = await _job(client, [field])
    application_id = await _apply(client, job, {field["id"]: "No"}, "out@example.com")

    completer = await _run(db_session, application_id)

    assert completer.calls == 0
    application = await applications_repo.get_by_id(db_session, application_id)
    assert application is not None
    assert application.status == ApplicationStatus.KNOCKED_OUT
    assert application.stop_reason == "Failed: Can you legally work in Pakistan?"


async def test_preferred_changes_answers_score_and_info_does_not(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    preferred = english_condition("preferred")
    info = yes_no_condition("travel", "info", "Can you travel up to 30% of the time?")
    job = await _job(client, [preferred, info])

    scores: dict[tuple[str, str], int | None] = {}
    for index, (level, travel) in enumerate(
        [("Fluent", "Yes"), ("Fluent", "No"), ("Basic", "Yes")]
    ):
        application_id = await _apply(
            client,
            job,
            {preferred["id"]: level, info["id"]: travel},
            f"candidate{index}@example.com",
        )
        await _run(db_session, application_id)
        scores[(level, travel)] = (await _detail(client, application_id))["answers_score"]

    assert scores[("Fluent", "Yes")] == scores[("Fluent", "No")] == 100
    assert scores[("Basic", "Yes")] == 0


async def test_detail_shows_condition_importance_and_verdict(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    must, preferred = _auth(), salary_condition("preferred")
    info = yes_no_condition("travel", "info", "Can you travel?")
    job = await _job(client, [must, preferred, info])
    application_id = await _apply(
        client,
        job,
        {must["id"]: "Yes", preferred["id"]: 500_000, info["id"]: "No"},
        "detail@example.com",
    )
    await _run(db_session, application_id)

    answers = (await _detail(client, application_id))["answers"]

    assert [(item["condition"]["importance"], item["condition_verdict"]) for item in answers] == [
        ("must", "pass"),
        ("preferred", "partial"),
        ("info", "not_scored"),
    ]
    assert answers[1]["condition"]["salary"] == {"currency": "PKR", "min": 150000, "max": 250000}


# --- recruiter and candidate views ---------------------------------------------------


async def test_public_job_lists_must_conditions_before_you_apply(client: AsyncClient) -> None:
    must = _auth()
    preferred = english_condition("preferred")
    job = await _job(client, [must, preferred])

    response = await client.get(f"{settings.API_V1_STR}/public/jobs/{job['public_slug']}")

    body = response.json()
    assert body["before_you_apply"] == ["Can you legally work in Pakistan? summary"]
    for field in body["form_fields"]:
        assert field["condition"] is None
        assert field["knockout"] is None
        assert field["scoring"] is None


async def test_job_detail_counts_stopped_and_moved_forward(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    auth, english = _auth(), english_condition("must")
    job = await _job(client, [auth, english])
    answers = [
        {auth["id"]: "No", english["id"]: "Fluent"},
        {auth["id"]: "No", english["id"]: "Basic"},
        {auth["id"]: "Yes", english["id"]: "Fluent"},
    ]
    ids = [
        await _apply(client, job, item, f"count{index}@example.com")
        for index, item in enumerate(answers)
    ]
    for application_id in ids:
        await _run(db_session, application_id)
    moved = await client.post(f"{settings.API_V1_STR}/applications/{ids[0]}/move-forward")
    assert moved.status_code == 200

    detail = await client.get(f"{settings.API_V1_STR}/jobs/{job['id']}")

    counts = {
        item["field_id"]: (item["stopped"], item["moved_forward"])
        for item in detail.json()["condition_knockouts"]
    }
    assert counts == {auth["id"]: (2, 1), english["id"]: (1, 0)}


async def test_export_includes_condition_answers_and_stopping_condition(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    auth, info = _auth(), yes_no_condition("travel", "info", "Can you travel?")
    job = await _job(client, [auth, info])
    application_id = await _apply(
        client, job, {auth["id"]: "No", info["id"]: "Yes"}, "export@example.com"
    )
    await _run(db_session, application_id)

    response = await client.post(
        f"{settings.API_V1_STR}/jobs/{job['id']}/exports",
        json={"application_ids": [str(application_id)]},
    )

    rows = list(csv.reader(io.StringIO(response.text)))
    header, row = rows[1], rows[2]
    assert header[8:] == [
        "stopped by condition",
        "Can you legally work in Pakistan? (Must)",
        "Can you travel? (Info only)",
    ]
    assert row[8:] == ["Can you legally work in Pakistan?", "No", "Yes"]


# --- blind scoring --------------------------------------------------------------------


async def test_model_sees_redacted_text_and_recruiter_keeps_original(
    client: AsyncClient, db_session: AsyncSession
) -> None:
    job = await _job(client, [])
    application_id = await _apply(client, job, {}, "blind@example.com")

    completer = await _run(db_session, application_id)

    [sent] = completer.sent
    assert "14-08-1995" not in sent and "35202-1234567-1" not in sent
    assert sent.count(PLACEHOLDER) == 2
    assert RESUME_TEXT in sent
    application = await applications_repo.get_by_id(db_session, application_id)
    assert application is not None
    assert application.extracted_text == PERSONAL_RESUME
    resume_row = (await _phase_rows(db_session, application_id))[-1]
    assert resume_row.evidence["redacted_lines"] == 2
    assert "14-08-1995" not in str(resume_row.evidence)
