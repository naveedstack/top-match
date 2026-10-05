import secrets
from uuid import UUID, uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Application, ApplicationStatus, Job, JobStatus, Recruiter

JOB_BODY = {
    "title": "Senior Engineer",
    "description": "Build the screening middleware",
    "requirements": "Python, FastAPI, PostgreSQL",
}


async def _create_job(client: AsyncClient) -> dict[str, object]:
    response = await client.post(f"{settings.API_V1_STR}/jobs", json=JOB_BODY)
    assert response.status_code == 201
    return response.json()


async def _insert_job(db_session: AsyncSession, owner: Recruiter, title: str = "Other job") -> Job:
    job = Job(
        recruiter_id=owner.id,
        title=title,
        description="Owned by someone else",
        requirements="N/A",
        public_slug=secrets.token_urlsafe(8),
        status=JobStatus.OPEN,
    )
    db_session.add(job)
    await db_session.flush()
    return job


async def test_create_job_returns_public_apply_url(client: AsyncClient) -> None:
    payload = await _create_job(client)

    assert payload["title"] == JOB_BODY["title"]
    assert payload["status"] == "open"
    assert payload["closed_at"] is None
    slug = payload["public_slug"]
    assert isinstance(slug, str) and slug
    assert payload["company_slug"] == "test-recruiter"
    assert payload["public_url"] == f"{settings.PUBLIC_APP_URL}/test-recruiter/{slug}"


async def test_list_jobs_is_scoped_to_current_recruiter(
    client: AsyncClient,
    db_session: AsyncSession,
    other_recruiter: Recruiter,
) -> None:
    created = await _create_job(client)
    await _insert_job(db_session, other_recruiter)

    response = await client.get(f"{settings.API_V1_STR}/jobs")

    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 1
    assert jobs[0]["id"] == created["id"]
    assert jobs[0]["application_counts"] == {
        "received": 0,
        "processing": 0,
        "scored": 0,
        "refused": 0,
        "failed": 0,
    }


async def test_list_jobs_includes_application_counts(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    created = await _create_job(client)
    job_id = UUID(str(created["id"]))
    statuses = [
        ApplicationStatus.RECEIVED,
        ApplicationStatus.RECEIVED,
        ApplicationStatus.PROCESSING,
        ApplicationStatus.SCORED,
        ApplicationStatus.REFUSED,
        ApplicationStatus.FAILED,
    ]
    for index, status in enumerate(statuses):
        db_session.add(
            Application(
                job_id=job_id,
                email=f"candidate{index}@example.com",
                status=status,
            )
        )
    await db_session.flush()

    response = await client.get(f"{settings.API_V1_STR}/jobs")

    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 1
    assert jobs[0]["application_counts"] == {
        "received": 2,
        "processing": 1,
        "scored": 1,
        "refused": 1,
        "failed": 1,
    }


async def test_job_detail_includes_zero_application_counts(client: AsyncClient) -> None:
    created = await _create_job(client)

    response = await client.get(f"{settings.API_V1_STR}/jobs/{created['id']}")

    assert response.status_code == 200
    body = response.json()
    assert body["application_counts"] == {
        "received": 0,
        "processing": 0,
        "scored": 0,
        "refused": 0,
        "failed": 0,
    }


async def test_other_recruiters_job_is_not_found(
    client: AsyncClient,
    db_session: AsyncSession,
    other_recruiter: Recruiter,
) -> None:
    foreign = await _insert_job(db_session, other_recruiter)
    job_url = f"{settings.API_V1_STR}/jobs/{foreign.id}"

    get_response = await client.get(job_url)
    patch_response = await client.patch(job_url, json={"title": "Hijack"})
    close_response = await client.post(f"{job_url}/close")

    assert get_response.status_code == 404
    assert patch_response.status_code == 404
    assert close_response.status_code == 404


async def test_unknown_job_is_not_found(client: AsyncClient) -> None:
    response = await client.get(f"{settings.API_V1_STR}/jobs/{uuid4()}")
    assert response.status_code == 404


async def test_public_job_returns_only_public_fields(client: AsyncClient) -> None:
    created = await _create_job(client)

    response = await client.get(f"{settings.API_V1_STR}/public/jobs/{created['public_slug']}")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {
        "title",
        "description",
        "requirements",
        "form_fields",
        "company_slug",
        "status",
        "privacy_notice",
        "ai_screening_notice",
        "screening_disclaimer",
    }
    assert body["form_fields"] == []
    assert body["title"] == JOB_BODY["title"]
    assert body["description"] == JOB_BODY["description"]
    assert body["requirements"] == JOB_BODY["requirements"]
    assert body["company_slug"] == "test-recruiter"
    assert body["status"] == "open"


async def test_unknown_public_slug_is_not_found(client: AsyncClient) -> None:
    response = await client.get(f"{settings.API_V1_STR}/public/jobs/does-not-exist")
    assert response.status_code == 404


async def test_close_job_is_idempotent(client: AsyncClient) -> None:
    created = await _create_job(client)

    first = await client.post(f"{settings.API_V1_STR}/jobs/{created['id']}/close")
    second = await client.post(f"{settings.API_V1_STR}/jobs/{created['id']}/close")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["status"] == "closed"
    assert first.json()["closed_at"] is not None
    assert second.json()["closed_at"] == first.json()["closed_at"]


async def test_closed_job_still_visible_on_public_page(client: AsyncClient) -> None:
    created = await _create_job(client)
    await client.post(f"{settings.API_V1_STR}/jobs/{created['id']}/close")

    response = await client.get(f"{settings.API_V1_STR}/public/jobs/{created['public_slug']}")

    assert response.status_code == 200
    assert response.json()["status"] == "closed"


async def test_patch_updates_fields_but_not_slug(client: AsyncClient) -> None:
    created = await _create_job(client)
    original_slug = created["public_slug"]

    response = await client.patch(
        f"{settings.API_V1_STR}/jobs/{created['id']}",
        json={"title": "Staff Engineer"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Staff Engineer"
    assert body["public_slug"] == original_slug
    assert body["description"] == JOB_BODY["description"]


async def test_patch_rejects_slug_changes(client: AsyncClient) -> None:
    created = await _create_job(client)

    response = await client.patch(
        f"{settings.API_V1_STR}/jobs/{created['id']}",
        json={"public_slug": "taken-over"},
    )

    assert response.status_code == 422
