from httpx import AsyncClient

from app.core.config import settings
from app.core.rate_limit import limiter

REGISTER_BODY = {
    "company_name": "Acme Hiring",
    "email": "recruiter@acme.com",
    "password": "password12",
}

JOB_BODY = {
    "title": "Senior Engineer",
    "description": "Build the screening middleware",
    "requirements": "Python, FastAPI, PostgreSQL",
}


async def _register(client: AsyncClient) -> dict[str, object]:
    response = await client.post(f"{settings.API_V1_STR}/auth/register", json=REGISTER_BODY)
    assert response.status_code == 201
    return response.json()


async def test_register_returns_profile_and_tokens(anonymous_client: AsyncClient) -> None:
    body = await _register(anonymous_client)

    assert body["company_name"] == REGISTER_BODY["company_name"]
    assert body["email"] == REGISTER_BODY["email"]
    assert isinstance(body["id"], str)
    assert body["access_token"]
    assert body["refresh_token"]


async def test_register_succeeds_with_rate_limiter_enabled(
    anonymous_client: AsyncClient,
) -> None:
    limiter.enabled = True
    try:
        response = await anonymous_client.post(
            f"{settings.API_V1_STR}/auth/register", json=REGISTER_BODY
        )
    finally:
        limiter.enabled = False

    assert response.status_code == 201
    assert response.json()["email"] == REGISTER_BODY["email"]


async def test_register_duplicate_email(anonymous_client: AsyncClient) -> None:
    await _register(anonymous_client)

    response = await anonymous_client.post(
        f"{settings.API_V1_STR}/auth/register", json=REGISTER_BODY
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"


async def test_login_success(anonymous_client: AsyncClient) -> None:
    await _register(anonymous_client)

    response = await anonymous_client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": REGISTER_BODY["email"], "password": REGISTER_BODY["password"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["email"] == REGISTER_BODY["email"]
    assert body["access_token"]
    assert body["refresh_token"]


async def test_login_failure(anonymous_client: AsyncClient) -> None:
    await _register(anonymous_client)

    wrong_password = await anonymous_client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": REGISTER_BODY["email"], "password": "wrong-password"},
    )
    unknown_email = await anonymous_client.post(
        f"{settings.API_V1_STR}/auth/login",
        json={"email": "nobody@acme.com", "password": REGISTER_BODY["password"]},
    )

    assert wrong_password.status_code == 401
    assert unknown_email.status_code == 401
    assert wrong_password.json() == unknown_email.json()
    assert wrong_password.json()["detail"] == "Invalid email or password"


async def test_me_requires_access_token(anonymous_client: AsyncClient) -> None:
    created = await _register(anonymous_client)

    missing = await anonymous_client.get(f"{settings.API_V1_STR}/auth/me")
    with_refresh = await anonymous_client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": f"Bearer {created['refresh_token']}"},
    )
    with_access = await anonymous_client.get(
        f"{settings.API_V1_STR}/auth/me",
        headers={"Authorization": f"Bearer {created['access_token']}"},
    )

    assert missing.status_code == 401
    assert with_refresh.status_code == 401
    assert with_access.status_code == 200
    assert with_access.json() == {
        "id": created["id"],
        "company_name": REGISTER_BODY["company_name"],
        "email": REGISTER_BODY["email"],
    }


async def test_refresh_rotation_rejects_old_token(anonymous_client: AsyncClient) -> None:
    created = await _register(anonymous_client)
    old_refresh = created["refresh_token"]

    rotated = await anonymous_client.post(
        f"{settings.API_V1_STR}/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    reused = await anonymous_client.post(
        f"{settings.API_V1_STR}/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    next_pair = await anonymous_client.post(
        f"{settings.API_V1_STR}/auth/refresh",
        json={"refresh_token": rotated.json()["refresh_token"]},
    )

    assert rotated.status_code == 200
    assert rotated.json()["refresh_token"] != old_refresh
    assert reused.status_code == 401
    assert next_pair.status_code == 200


async def test_logout_revokes_refresh_token(anonymous_client: AsyncClient) -> None:
    created = await _register(anonymous_client)

    logout = await anonymous_client.post(
        f"{settings.API_V1_STR}/auth/logout",
        json={"refresh_token": created["refresh_token"]},
    )
    refresh = await anonymous_client.post(
        f"{settings.API_V1_STR}/auth/refresh",
        json={"refresh_token": created["refresh_token"]},
    )

    assert logout.status_code == 204
    assert refresh.status_code == 401


async def test_create_job_requires_auth(anonymous_client: AsyncClient) -> None:
    response = await anonymous_client.post(f"{settings.API_V1_STR}/jobs", json=JOB_BODY)

    assert response.status_code == 401
