from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

import jwt
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

from app.core.config import settings
from app.core.exceptions import InvalidTokenError

_password_hash = PasswordHash.recommended()
_JWT_ALGORITHM = "HS256"

# Used when the email is unknown so login timing stays close to a real verify.
_DUMMY_PASSWORD_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$AtF4TEXBCSXNLZzGmhn3OA$"
    "5G5PpiMm1nPXZt78YmLJhQy9vUL8Md2YX1M09BlNTgc"
)


def hash_password(password: str) -> str:
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _password_hash.verify(password, password_hash)
    except UnknownHashError:
        return False


def dummy_verify_password(password: str) -> None:
    verify_password(password, _DUMMY_PASSWORD_HASH)


def create_access_token(recruiter_id: UUID) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(recruiter_id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET.get_secret_value(), algorithm=_JWT_ALGORITHM)


def create_refresh_token(recruiter_id: UUID) -> tuple[str, str, datetime]:
    now = datetime.now(UTC)
    jti = str(uuid4())
    expires_at = now + timedelta(days=settings.REFRESH_TOKEN_DAYS)
    payload = {
        "sub": str(recruiter_id),
        "type": "refresh",
        "jti": jti,
        "iat": now,
        "exp": expires_at,
    }
    token = jwt.encode(payload, settings.JWT_SECRET.get_secret_value(), algorithm=_JWT_ALGORITHM)
    return jti, token, expires_at


def decode_access_token(token: str) -> UUID:
    payload = _decode(token)
    if payload.get("type") != "access":
        raise InvalidTokenError
    return _parse_sub(payload)


def decode_refresh_token(token: str) -> tuple[UUID, str]:
    payload = _decode(token)
    if payload.get("type") != "refresh":
        raise InvalidTokenError
    jti = payload.get("jti")
    if not isinstance(jti, str) or not jti:
        raise InvalidTokenError
    return _parse_sub(payload), jti


def _decode(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET.get_secret_value(),
            algorithms=[_JWT_ALGORITHM],
        )
    except jwt.PyJWTError as exc:
        raise InvalidTokenError from exc
    if not isinstance(payload, dict):
        raise InvalidTokenError
    return payload


def _parse_sub(payload: dict[str, Any]) -> UUID:
    sub = payload.get("sub")
    if not isinstance(sub, str):
        raise InvalidTokenError
    try:
        return UUID(sub)
    except ValueError as exc:
        raise InvalidTokenError from exc
