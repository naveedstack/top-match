from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services import screening_queue
from app.services.pipeline import process_application
from tests.api.test_applications import _apply
from tests.api.test_jobs import _create_job
from tests.api.test_pipeline import FakeCompleter


@pytest.fixture
def queued(monkeypatch: pytest.MonkeyPatch) -> list[tuple[UUID, bool]]:
    calls: list[tuple[UUID, bool]] = []

    def _enqueue(application_id: UUID, *, reclaim_processing: bool = False) -> None:
        calls.append((application_id, reclaim_processing))

    monkeypatch.setattr(screening_queue, "enqueue_screening", _enqueue)
    return calls


async def test_services_queue_screening_after_commit(
    client: AsyncClient, db_session: AsyncSession, queued: list[tuple[UUID, bool]]
) -> None:
    job = await _create_job(client)
    applied = await _apply(client, str(job["public_slug"]))
    application_id = UUID(applied.json()["id"])
    assert queued == [(application_id, False)]

    await process_application(application_id, db_session, completer=FakeCompleter(fail=True))
    retried = await client.post(f"{settings.API_V1_STR}/applications/{application_id}/rescore")

    assert retried.status_code == 200
    assert queued[-1] == (application_id, True)

    # Already processing: a second retry is rejected and nothing extra is queued.
    duplicate = await client.post(f"{settings.API_V1_STR}/applications/{application_id}/rescore")
    assert duplicate.status_code == 404
    assert len(queued) == 2


async def test_enqueue_is_a_no_op_when_pipeline_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    started: list[UUID] = []

    async def _process(application_id: UUID, **_kwargs: object) -> None:
        started.append(application_id)

    monkeypatch.setattr(screening_queue, "process_application", _process)

    screening_queue.enqueue_screening(uuid4())
    await screening_queue.drain()

    assert started == []


async def test_failed_task_logs_only_ids(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    secret = "Jane Doe, 12 Main St, jane@example.com"

    async def _boom(_application_id: UUID, **_kwargs: object) -> None:
        raise ValueError(secret)

    monkeypatch.setattr(settings, "PIPELINE_ENABLED", True)
    monkeypatch.setattr(screening_queue, "process_application", _boom)
    application_id = uuid4()

    screening_queue.enqueue_screening(application_id)
    await screening_queue.drain()

    assert str(application_id) in caplog.text
    assert "ValueError" in caplog.text
    assert secret not in caplog.text
