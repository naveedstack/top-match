from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.api.deps import get_current_recruiter, get_db
from app.core.config import settings
from app.core.rate_limit import limiter
from app.db.session import engine
from app.main import app
from app.models import Recruiter


@pytest.fixture(scope="session", autouse=True)
async def _dispose_engine() -> AsyncIterator[None]:
    yield
    await engine.dispose()


@pytest.fixture(autouse=True)
def isolated_storage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    root = tmp_path / "resumes"
    root.mkdir()
    monkeypatch.setattr(settings, "STORAGE_DIR", root)
    return root


@pytest.fixture(autouse=True)
def disable_rate_limiter() -> Iterator[None]:
    was_enabled = limiter.enabled
    limiter.enabled = False
    yield
    limiter.enabled = was_enabled


@pytest.fixture(autouse=True)
def disable_pipeline(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "PIPELINE_ENABLED", False)


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    async with engine.connect() as connection:
        transaction = await connection.begin()
        session = AsyncSession(bind=connection, expire_on_commit=False)
        await connection.begin_nested()

        @event.listens_for(session.sync_session, "after_transaction_end")
        def restart_savepoint(sync_session: Session, _transaction: object) -> None:
            if connection.closed:
                return
            sync_connection = connection.sync_connection
            if sync_connection is not None and not sync_connection.in_nested_transaction():
                sync_connection.begin_nested()

        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()


@pytest.fixture
async def recruiter(db_session: AsyncSession) -> Recruiter:
    record = Recruiter(
        email="recruiter@example.com",
        name="Test Recruiter",
        company_name="Test Recruiter",
        password_hash="!",
    )
    db_session.add(record)
    await db_session.flush()
    return record


@pytest.fixture
async def other_recruiter(db_session: AsyncSession) -> Recruiter:
    record = Recruiter(
        email="other@example.com",
        name="Other Recruiter",
        company_name="Other Recruiter",
        password_hash="!",
    )
    db_session.add(record)
    await db_session.flush()
    return record


@pytest.fixture
async def client(db_session: AsyncSession, recruiter: Recruiter) -> AsyncIterator[AsyncClient]:
    async def override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    async def override_get_current_recruiter() -> Recruiter:
        return recruiter

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_recruiter] = override_get_current_recruiter
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
async def anonymous_client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    async def override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
