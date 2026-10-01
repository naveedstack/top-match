from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InvalidTokenError
from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models import Recruiter
from app.repositories import recruiters as recruiters_repo

_bearer = HTTPBearer(auto_error=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


DbSession = Annotated[AsyncSession, Depends(get_db)]


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_recruiter(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> Recruiter:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()
    try:
        recruiter_id = decode_access_token(credentials.credentials)
    except InvalidTokenError as exc:
        raise _unauthorized() from exc
    recruiter = await recruiters_repo.get_by_id(db, recruiter_id)
    if recruiter is None:
        raise _unauthorized()
    return recruiter


CurrentRecruiter = Annotated[Recruiter, Depends(get_current_recruiter)]
