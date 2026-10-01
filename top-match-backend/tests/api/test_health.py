from httpx import AsyncClient

from app.core.config import settings


async def test_liveness(client: AsyncClient) -> None:
    response = await client.get(f"{settings.API_V1_STR}/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
