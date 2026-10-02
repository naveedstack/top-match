from contextvars import ContextVar, Token
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

_REQUEST_ID: ContextVar[str | None] = ContextVar("request_id", default=None)
_HEADER = "X-Request-ID"


def get_request_id() -> str | None:
    return _REQUEST_ID.get()


def set_request_id(request_id: str) -> Token[str | None]:
    return _REQUEST_ID.set(request_id)


def reset_request_id(token: Token[str | None]) -> None:
    _REQUEST_ID.reset(token)


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        incoming = request.headers.get(_HEADER, "").strip()
        request_id = incoming or str(uuid4())
        token = set_request_id(request_id)
        try:
            response = await call_next(request)
        finally:
            reset_request_id(token)
        response.headers[_HEADER] = request_id
        return response
