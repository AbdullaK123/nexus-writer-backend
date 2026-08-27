from httpx import AsyncClient


async def test_health_endpoint_returns_success(app_client: AsyncClient) -> None:
    response = await app_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"message": "Everything is healthy!"}
