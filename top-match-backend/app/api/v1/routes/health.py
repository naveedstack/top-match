from fastapi import APIRouter

from app.api.deps import DbSession
from app.api.v1.handlers.health import handler as health_handlers
from app.schemas.health import HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def liveness() -> HealthResponse:
    return await health_handlers.liveness()


@router.get("/ready")
async def readiness(db: DbSession) -> HealthResponse:
    return await health_handlers.readiness(db)
