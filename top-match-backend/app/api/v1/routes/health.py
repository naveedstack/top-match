from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.deps import DbSession
from app.schemas.health import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def liveness() -> HealthResponse:
    """The process is up and serving requests."""
    return HealthResponse(status="ok")


@router.get("/ready")
async def readiness(db: DbSession) -> HealthResponse:
    """The app can reach its dependencies (database)."""
    try:
        await db.execute(text("SELECT 1"))
    except (SQLAlchemyError, OSError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable"
        ) from exc
    return HealthResponse(status="ok")
